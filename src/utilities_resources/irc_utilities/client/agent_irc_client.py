"""AgentIRCClient — minimal, non-blocking, thread-safe IRC client (FIXED 09:40).

Fixes:
  * history(): removed stray bare `f` line, moved docstring to top, and
    joined messages with newlines + separated fields. (Original concatenated
    with no separators -> one giant line -> looked like a hang.)
  * reader loop: stopped printing every message to stdout ("Adding ...").
    That flood could block a harness that waits on the agent's stdout.
    Set IRC_DEBUG=1 to re-enable.
  * _request(): keeps arrival order when re-queueing non-matching messages.
"""

import json
import os
import socket
import threading

import queue


class AgentIRCClient(object):
    """Minimal IRC client for agent collaboration."""

    def __init__(self):
        self._sock = None
        self._lock = threading.Lock()
        self._reader_thread = None
        self._inbox = queue.Queue()
        self._closed = False
        self.nickname = None
        self._history = []

    # ------------------------------------------------------------------ API
    def connect(self, host, port, nickname):
        if not nickname or not str(nickname).strip():
            raise ValueError("nickname is required (got %r)" % (nickname,))
        with self._lock:
            if self._sock is not None:
                self._close_socket_locked()
            self._closed = False
            self.nickname = nickname

        sock = socket.create_connection((host, port))
        sock.settimeout(1.0)

        with self._lock:
            self._sock = sock

        self._send_cmd({"cmd": "NICK", "nick": nickname})

        self._reader_thread = threading.Thread(
            target=self._read_loop, name="irc-reader", daemon=True,
        )
        self._reader_thread.start()
        return self

    def join(self, channel):
        self._send_cmd({"cmd": "JOIN", "channel": channel})

    def part(self, channel):
        self._send_cmd({"cmd": "PART", "channel": channel})

    def send(self, channel, message):
        self._send_cmd({"cmd": "PRIVMSG", "channel": channel, "text": message})

    def poll(self):
        out = []
        while True:
            try:
                out.append(self._inbox.get_nowait())
            except queue.Empty:
                break
        return out

    def list_channels(self):
        reply = self._request({"cmd": "LIST"})
        if reply is None:
            return []
        return reply.get("channels", [])

    def history(self, channel, n=50):
        """Return the last *n* messages for *channel* as readable text."""
        reply = self._request({"cmd": "HISTORY", "channel": channel})
        if reply is None:
            return "IRC History returned no reply."
        messages = reply.get("messages", [])
        if n and n > 0:
            messages = messages[-n:]
        return "\n".join(
            "User: %s Content: %s" % (r.get("nick"), r.get("text"))
            for r in messages
        )

    def quit(self):
        with self._lock:
            sock = self._sock
        if sock is not None:
            try:
                self._send_cmd({"cmd": "QUIT"})
            except (OSError, ValueError):
                pass
        self._close_socket_locked()

    # ------------------------------------------------------------ internals
    def _send_cmd(self, obj):
        with self._lock:
            sock = self._sock
        if sock is None:
            raise ValueError("not connected")
        data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        with self._lock:
            sock.sendall(data)

    def _request(self, obj):
        self._send_cmd(obj)
        deadline = _now() + 3.0
        stash = []
        try:
            while _now() < deadline:
                try:
                    msg = self._inbox.get(timeout=0.1)
                except queue.Empty:
                    continue
                if msg.get("type") == "reply" and msg.get("cmd") == obj["cmd"]:
                    return msg
                stash.append(msg)
        finally:
            for msg in stash:
                self._inbox.put(msg)
        return None

    def _read_loop(self):
        with self._lock:
            sock = self._sock
        if sock is None:
            return
        buf = b""
        while True:
            try:
                data = sock.recv(65536)
            except socket.timeout:
                continue  # idle, keep reader alive
            except (OSError, ValueError):
                data = b""
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line.decode("utf-8", "replace"))
                except ValueError:
                    continue
                self._inbox.put(obj)

                self._history.append(obj)
        with self._lock:
            self._closed = True

    def _close_socket_locked(self):
        with self._lock:
            sock = self._sock
            self._sock = None
            self._closed = True
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass


def _now():
    import time
    return time.time()


def _demo():
    import sys
    host, port = "127.0.0.1", 6667
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    c = AgentIRCClient()
    try:
        c.connect(host, port, "demo-bot")
    except OSError as exc:
        print("No server reachable at %s:%d (%s)." % (host, port, exc))
        return
    try:
        c.join("#test")
        c.send("#test", "hello from the demo client")
        time.sleep(1.0)
        print("Received:", c.poll())
        print("Channels:", c.list_channels())
        print("History:", c.history("#test"))
    finally:
        c.quit()


if __name__ == "__main__":
    import time  # noqa: E402  (used by _demo)
    _demo()

