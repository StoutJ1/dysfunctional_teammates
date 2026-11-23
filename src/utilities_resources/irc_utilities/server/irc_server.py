#!/usr/bin/env python3
"""
irc_server.py - A minimal IRC-like server for agent collaboration.

This is a single-file, stdlib-only server exposing a simple newline-delimited
JSON protocol. Clients connect over TCP, set a NICK, join CHANNELs, and send
PRIVMSGs which are routed (thread-safely) to all other members of the channel.

Every significant event (connect, nick, join, part, message, history request,
quit) is appended to a JSONL log file for observability.

Protocol (one JSON object per line, terminated by '\n'):

    -> {"cmd": "NICK",    "nick": "alice"}
    -> {"cmd": "JOIN",    "channel": "#general"}
    -> {"cmd": "PART",    "channel": "#general"}
    -> {"cmd": "PRIVMSG", "channel": "#general", "text": "hello"}
    -> {"cmd": "LIST"}                              (list channels + members)
    -> {"cmd": "HISTORY", "channel": "#general"}    (recent messages)
    -> {"cmd": "QUIT"}

Server responses are also newline-delimited JSON objects of the form:

    {"type": "event"}            e.g. NICK, JOIN, PART, PRIVMSG, PART/QUIT
    {"type": "reply", ...}       LIST / HISTORY results
    {"type": "error", "error": "..."}

Usage:
    python irc_server.py [--host 127.0.0.1] [--port 6667] [--log irc_server.log]
"""

import argparse
import json
import select
import socket
import threading
import time


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class JsonlLogger:
    """Thread-safe JSONL event logger."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()

        # Open in append mode so the log survives restarts. We keep the file
        # handle open and flush on every write to guarantee events are on disk.
        self._fh = open(path, "a", encoding="utf-8")

    def log(self, event_type, **fields):
        """Write a single event record to the JSONL file."""
        record = {
            "ts": time.time(),
            "event": event_type,
        }
        record.update(fields)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        with self._lock:
            self._fh.write(line + "\n")
            self._fh.flush()


# ---------------------------------------------------------------------------
# The server
# ---------------------------------------------------------------------------

class IrcServer:
    """Core IRC-like server engine."""

    HOST = "127.0.0.1"
    PORT = 6667
    LOG_PATH = "irc_server.log"
    HISTORY_LIMIT = 100

    def __init__(self, host=None, port=None, log_path=None):
        self.host = host or self.HOST
        self.port = port or self.PORT
        self.logger = JsonlLogger(log_path or self.LOG_PATH)

        # Global lock guarding all shared mutable state below.
        self._lock = threading.RLock()

        # socket -> ClientSession
        self._clients = {}

        # nick (lowercased for lookup) -> ClientSession
        self._nicks = {}

        # channel name (lowercased) -> {nick (canonical) : ClientSession}
        self._channels = {}

        # channel name (lowercased) -> list of recent messages (list of dicts)
        self._history = {}

        self._running = False
        self._server_sock = None
        self._inputs = []  # sockets monitored for readability (incl. wakeup)

    # ------------------------------------------------------------------ state
    def _broadcast(self, channel, message):
        """Send `message` to every client currently in `channel`."""
        canonical = self._canonical_channel_name(channel)
        senders = []
        with self._lock:
            members = self._channels.get(canonical, {})
            for client in list(members.values()):
                senders.append(client)
        for client in senders:
            client.send(message)

    def _canonical_channel_name(self, channel):
        return str(channel).lower()

    def _canonical_nick(self, nick):
        return str(nick).lower()

    # -------------------------------------------------------------- handlers
    def _handle_message(self, client, data):
        """Parse a single line of JSON and dispatch it."""
        try:
            obj = json.loads(data)
        except (ValueError, TypeError):
            client.send_error("invalid JSON")
            return

        if not isinstance(obj, dict):
            client.send_error("message must be a JSON object")
            return

        cmd = obj.get("cmd")
        if cmd is None:
            client.send_error("missing field: cmd")
            return

        handler = getattr(self, "_cmd_" + str(cmd).upper(), None)
        if handler is None:
            client.send_error("unknown command: %s" % cmd)
            return

        try:
            handler(client, obj)
        except Exception as exc:  # never let a handler crash the server
            self.logger.log("server_error", error=str(exc))
            client.send_error("internal error: %s" % exc)

    def _cmd_NICK(self, client, obj):
        nick = obj.get("nick")
        if not nick or not isinstance(nick, str):
            client.send_error("NICK requires a string 'nick'")
            return
        nick = nick.strip()
        if not nick:
            client.send_error("empty nick")
            return

        canonical = self._canonical_nick(nick)
        with self._lock:
            if canonical in self._nicks and self._nicks[canonical] is not client:
                client.send_error("nick already in use: %s" % nick)
                return

            old_nick = client.nick
            if old_nick is not None:
                del self._nicks[self._canonical_nick(old_nick)]

            client.nick = nick
            self._nicks[canonical] = client

        self.logger.log("nick", nick=nick)
        client.send({"type": "event", "event": "NICK", "nick": nick})

    def _cmd_JOIN(self, client, obj):
        channel = obj.get("channel")
        if not channel or not isinstance(channel, str):
            client.send_error("JOIN requires a string 'channel'")
            return
        # Ensure a nick is set before joining.
        if client.nick is None:
            client.send_error("must set NICK before JOIN")
            return

        canonical = self._canonical_channel_name(channel)
        with self._lock:
            c = self._channels.setdefault(canonical, {})
            c[client.nick] = client
            if canonical not in self._history:
                self._history[canonical] = []
            names = sorted(c.keys())

        self.logger.log("join", channel=channel, nick=client.nick)

        # Tell the joiner who is in the room.
        client.send({
            "type": "reply",
            "cmd": "JOIN",
            "channel": channel,
            "members": names,
        })
        # Tell everyone else someone joined.
        self._broadcast(channel, {
            "type": "event",
            "event": "JOIN",
            "channel": channel,
            "nick": client.nick,
        })

    def _cmd_PART(self, client, obj):
        channel = obj.get("channel")
        if not channel or not isinstance(channel, str):
            client.send_error("PART requires a string 'channel'")
            return
        canonical = self._canonical_channel_name(channel)
        with self._lock:
            c = self._channels.get(canonical)
            if c is None or client.nick not in c:
                client.send_error("not in channel: %s" % channel)
                return
            del c[client.nick]
            if not c:
                del self._channels[canonical]

        self.logger.log("part", channel=channel, nick=client.nick)
        self._broadcast(channel, {
            "type": "event",
            "event": "PART",
            "channel": channel,
            "nick": client.nick,
        })
        client.send({
            "type": "event",
            "event": "PART",
            "channel": channel,
            "nick": client.nick,
        })

    def _cmd_PRIVMSG(self, client, obj):
        channel = obj.get("channel")
        text = obj.get("text")
        if not channel or not isinstance(channel, str):
            client.send_error("PRIVMSG requires a string 'channel'")
            return
        if text is None or not isinstance(text, str):
            client.send_error("PRIVMSG requires a string 'text'")
            return
        canonical = self._canonical_channel_name(channel)

        # Require membership.
        with self._lock:
            c = self._channels.get(canonical)
            if c is None or client.nick not in c:
                client.send_error("not in channel: %s" % channel)
                return

            # Record history.
            record = {
                "ts": time.time(),
                "nick": client.nick,
                "channel": channel,
                "text": text,
            }
            self._history.setdefault(canonical, []).append(record)
            # Keep history bounded.
            if len(self._history[canonical]) > self.HISTORY_LIMIT:
                self._history[canonical] = self._history[canonical][
                    -self.HISTORY_LIMIT:
                ]

        self.logger.log("privmsg", nick=client.nick, channel=channel, text=text)

        self._broadcast(channel, {
            "type": "event",
            "event": "PRIVMSG",
            "channel": channel,
            "nick": client.nick,
            "text": text,
            "ts": record["ts"],
        })

    def _cmd_LIST(self, client, obj):
        with self._lock:
            channels = []
            for canonical, members in sorted(self._channels.items()):
                channels.append({
                    "channel": canonical,
                    "members": sorted(members.keys()),
                })
        self.logger.log("list", nick=client.nick)
        client.send({"type": "reply", "cmd": "LIST", "channels": channels})

    def _cmd_HISTORY(self, client, obj):
        channel = obj.get("channel")
        if not channel or not isinstance(channel, str):
            client.send_error("HISTORY requires a string 'channel'")
            return
        canonical = self._canonical_channel_name(channel)
        with self._lock:
            history = list(self._history.get(canonical, []))
        self.logger.log("history", nick=client.nick, channel=channel)
        client.send({
            "type": "reply",
            "cmd": "HISTORY",
            "channel": channel,
            "messages": history,
        })

    def _cmd_QUIT(self, client, obj):
        self._disconnect(client, reason="quit")

    # --------------------------------------------------------------- plumbing
    def _disconnect(self, client, reason="quit"):
        """Remove a client from all channels and close its socket."""
        sock = client.sock

        with self._lock:
            # Remove from channels and notify remaining members.
            for canonical, members in list(self._channels.items()):
                if client.nick in members:
                    del members[client.nick]
                    if not members:
                        del self._channels[canonical]
                    self.logger.log("part", channel=canonical,
                                    nick=client.nick, reason=reason)
                    self._broadcast(canonical, {
                        "type": "event",
                        "event": "PART",
                        "channel": canonical,
                        "nick": client.nick,
                    })
            # Remove nick registration and client registration.
            if client.nick is not None:
                self._nicks.pop(self._canonical_nick(client.nick), None)
            self._clients.pop(sock, None)

        # Make sure the socket is no longer monitored for reads, so select()
        # does not choke on a closed file descriptor.
        if sock in self._inputs:
            self._inputs.remove(sock)

        if client.nick is not None:
            self.logger.log("quit", nick=client.nick, reason=reason)
        client.close()

    # ------------------------------------------------------------------- run
    def start(self):
        """Bind the listening socket and enter the accept loop (blocking)."""
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(64)
        self._server_sock.setblocking(False)

        # Wakeup socketpair so other threads can interrupt select().
        wake_r, wake_w = socket.socketpair()
        wake_r.setblocking(False)
        wake_w.setblocking(False)
        self._wake_r = wake_r
        self._wake_w = wake_w

        self._running = True
        self._inputs = [self._server_sock, wake_r]
        self.logger.log("server_start", host=self.host, port=self.port)
        print("IRC server listening on %s:%d" % (self.host, self.port))

        try:
            while self._running:
                # Rebuild the output list each iteration from clients with
                # pending data. This is simple, correct, and also catches
                # messages queued via _broadcast earlier in the same loop.
                outputs = []
                with self._lock:
                    for c in self._clients.values():
                        if c.has_pending():
                            outputs.append(c.sock)

                readable, writable, _ = select.select(
                    self._inputs, outputs, [], 1.0)

                for s in readable:
                    if s is self._server_sock:
                        self._accept(s)
                    elif s is wake_r:
                        # Drain wakeup pipe (woken from another thread).
                        try:
                            while True:
                                chunk = wake_r.recv(1024)
                                if len(chunk) < 1024:
                                    break
                        except (OSError, BlockingIOError):
                            pass
                    else:
                        self._read_client(s)

                for s in writable:
                    self._flush_client(s)
        finally:
            self._shutdown()

    def _accept(self, server_sock):
        conn, addr = server_sock.accept()
        conn.setblocking(False)
        client = ClientSession(conn, addr, self)
        with self._lock:
            self._clients[conn] = client
        self._inputs.append(conn)
        self.logger.log("connect", addr="%s:%d" % addr)

    def _read_client(self, sock):
        client = self._clients.get(sock)
        if client is None:
            # Socket may have been removed already; drop from inputs.
            if sock in self._inputs:
                self._inputs.remove(sock)
            return
        try:
            data = sock.recv(65536)
        except (ConnectionError, OSError):
            data = b""

        if not data:
            # client disconnected
            self._disconnect(client, reason="disconnect")
            return

        client.buffer += data

        # Process complete newline-delimited lines.
        while b"\n" in client.buffer:
            line, client.buffer = client.buffer.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            self._handle_message(client, line.decode("utf-8", "replace"))

    def _flush_client(self, sock):
        client = self._clients.get(sock)
        if client is None:
            return
        try:
            client.flush()
        except (ConnectionError, OSError):
            self._disconnect(client, reason="disconnect")

    def _shutdown(self):
        self._running = False
        with self._lock:
            clients = list(self._clients.values())
        for client in clients:
            self._disconnect(client, reason="shutdown")
        if self._server_sock is not None:
            try:
                self._server_sock.close()
            except OSError:
                pass
        for s in (getattr(self, "_wake_r", None), getattr(self, "_wake_w", None)):
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
        self.logger.log("server_stop")


class ClientSession:
    """Per-connection state: socket, buffered input/output, and nick."""

    def __init__(self, sock, addr, server):
        self.sock = sock
        self.addr = addr
        self.server = server
        self.nick = None
        self.buffer = b""
        self._out_buffer = bytearray()
        self._lock = threading.Lock()

    def send(self, obj):
        """Queue a JSON object to be sent to this client."""
        line = json.dumps(obj, ensure_ascii=False) + "\n"
        with self._lock:
            self._out_buffer += line.encode("utf-8")

    def send_error(self, message):
        self.send({"type": "error", "error": message})

    def has_pending(self):
        with self._lock:
            return len(self._out_buffer) > 0

    def flush(self):
        with self._lock:
            if not self._out_buffer:
                return
            data = bytes(self._out_buffer)
            self._out_buffer = bytearray()

        total = len(data)
        sent = 0
        while sent < total:
            n = self.sock.send(data[sent:])
            if n <= 0:
                raise ConnectionError("send returned 0")
            sent += n

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Minimal IRC-like server for agent collaboration."
    )
    parser.add_argument("--host", default=IrcServer.HOST,
                        help="address to bind (default: %(default)s)")
    parser.add_argument("--port", type=int, default=IrcServer.PORT,
                        help="port to bind (default: %(default)s)")
    parser.add_argument("--log", default=IrcServer.LOG_PATH,
                        help="JSONL log path (default: %(default)s)")
    args = parser.parse_args(argv)

    server = IrcServer(host=args.host, port=args.port, log_path=args.log)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server._shutdown()


if __name__ == "__main__":
    main()

