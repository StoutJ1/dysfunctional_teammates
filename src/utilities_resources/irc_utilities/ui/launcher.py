#!/usr/bin/env python3
"""
launcher.py - dear_pygui launcher + observability UI for the agent IRC server.

This module:
  * imports the server engine from the sibling module (shared_space/v1/server).
  * lets the user pick host/port and Start/Stop the server (on a daemon thread
    so the UI thread stays responsive).
  * tails the server's JSONL log file live and renders it in a scrolling panel.
  * shows connected clients and channels, refreshable on demand (or on a timer).
  * mirrors UI-level log lines to an optional launcher log file.

The whole thing is self-contained and runnable via `python launcher.py`.
"""

import json
import os
import sys
import threading
import time

import dearpygui.dearpygui as dpg

# Add the server package directory to sys.path and import the engine. The
# server lives one directory up under "server/".
_SERVER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server")
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from irc_server import IrcServer  # noqa: E402

# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------

DEFAULT_HOST = IrcServer.HOST            # "127.0.0.1"
DEFAULT_PORT = IrcServer.PORT            # 6667
DEFAULT_LOG_PATH = os.path.join(_SERVER_DIR, IrcServer.LOG_PATH)

# Optional launcher-specific log (UI + lifecycle events only, not server JSONL).
_LAUNCHER_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "launcher.log")

# Cap on how many text lines the log panel keeps in memory / renders.
LOG_LINE_LIMIT = 2000

# dearpygui tag namespace (prefixed to avoid collisions).
_TAG = "irc_launcher"


# ---------------------------------------------------------------------------
# Launcher application state
# ---------------------------------------------------------------------------

class LauncherState:
    """Holds the server instance, its thread, and the log tail position."""

    def __init__(self):
        self.server = None
        self.thread = None
        self.log_offset = 0          # byte offset into the JSONL log
        self.launcher_log_fh = None  # optional launcher log handle


STATE = LauncherState()

# Timestamp of the last clients/channels status refresh.
STATE.last_status_refresh = 0.0


# ---------------------------------------------------------------------------
# UI logging helper
# ---------------------------------------------------------------------------

def ui_log(message):
    """Append a line to the in-UI log widget and mirror to the launcher log."""
    ts = time.strftime("%H:%M:%S")
    line = "[%s] %s" % (ts, message)

    # Mirror to the launcher's own file log (optional, best-effort).
    if STATE.launcher_log_fh is not None:
        try:
            STATE.launcher_log_fh.write(line + "\n")
            STATE.launcher_log_fh.flush()
        except OSError:
            pass

    # Render into the UI log widget if it exists yet.
    if dpg.does_item_exist(_TAG + ".log_text"):
        dpg.add_text(line, parent=_TAG + ".log_text")
        _trim_log_widget()


def _trim_log_widget():
    """Remove oldest lines beyond LOG_LINE_LIMIT to bound memory usage."""
    parent = _TAG + ".log_text"
    if not dpg.does_item_exist(parent):
        return
    children = dpg.get_item_children(parent, 1)
    kids = children[0] if len(children) == 2 else children
    excess = len(kids) - LOG_LINE_LIMIT
    for i in range(excess):
        if kids and dpg.does_item_exist(kids[i]):
            dpg.delete_item(kids[i])


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def _start_server_thread():
    """Run the server's blocking start() loop on the current thread."""
    server = STATE.server
    try:
        server.start()
    except Exception as exc:  # noqa: BLE001 - surface any bind/loop error in UI
        ui_log("Server thread error: %s" % exc)


def on_start(sender, app_data, user_data):
    """Callback for the Start button: spawn the server on a daemon thread."""
    if STATE.server is not None:
        ui_log("Server already running")
        return

    host = dpg.get_value(_TAG + ".host")
    port = int(dpg.get_value(_TAG + ".port"))
    log_path = dpg.get_value(_TAG + ".log_path")

    # Note: the server treats falsy host/port as "use default"; normalize here.
    host = host.strip() or DEFAULT_HOST
    if port <= 0:
        port = DEFAULT_PORT
    log_path = log_path.strip() or DEFAULT_LOG_PATH

    try:
        server = IrcServer(host=host, port=port, log_path=log_path)
    except OSError as exc:
        ui_log("Could not open log file %s: %s" % (log_path, exc))
        return

    STATE.server = server
    STATE.log_offset = 0  # new server -> new log (or same file, tail from here)

    STATE.thread = threading.Thread(
        target=_start_server_thread,
        name="irc-server",
        daemon=True,
    )
    STATE.thread.start()

    ui_log("Started IRC server on %s:%d (log: %s)" % (host, port, log_path))
    dpg.configure_item(_TAG + ".start", enabled=False)
    dpg.configure_item(_TAG + ".stop", enabled=True)


def on_stop(sender, app_data, user_data):
    """Callback for the Stop button: ask the server loop to shut down."""
    server = STATE.server
    if server is None:
        ui_log("Server is not running")
        return

    ui_log("Stopping IRC server ...")
    # _shutdown() flips _running and closes sockets; the select loop exits.
    try:
        server._shutdown()
    except Exception as exc:  # noqa: BLE001
        ui_log("Error during shutdown: %s" % exc)

    STATE.server = None
    STATE.thread = None
    dpg.configure_item(_TAG + ".start", enabled=True)
    dpg.configure_item(_TAG + ".stop", enabled=False)


# ---------------------------------------------------------------------------
# Log file tailing
# ---------------------------------------------------------------------------

def _tail_log():
    """Read any new bytes appended to the JSONL log and render them."""
    server = STATE.server
    if server is None:
        return

    log_path = server.logger.path
    try:
        if not os.path.exists(log_path):
            return
        size = os.path.getsize(log_path)
        if size < STATE.log_offset:
            # Log was truncated/rotated; restart from the beginning.
            STATE.log_offset = 0
        if size == STATE.log_offset:
            return
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(STATE.log_offset)
            data = fh.read()
            STATE.log_offset = fh.tell()
    except OSError:
        return

    for raw_line in data.splitlines():
        line = raw_line.rstrip("\n")
        if not line:
            continue
        ui_log(_format_log_line(line))


def _format_log_line(line):
    """Pretty-print a single JSONL record; fall back to raw text."""
    try:
        obj = json.loads(line)
    except (ValueError, TypeError):
        return line

    ts = obj.get("ts")
    when = ""
    if isinstance(ts, (int, float)):
        when = time.strftime("%H:%M:%S", time.localtime(ts)) + " "

    event = obj.get("event", "?")
    # Build a compact "key=value" description of the remaining fields.
    parts = [str(k) + "=" + str(v) for k, v in obj.items()
             if k not in ("ts", "event")]
    suffix = ("  " + " ".join(parts)) if parts else ""
    return "%s%-10s%s" % (when, event, suffix)


# ---------------------------------------------------------------------------
# Clients / channels panel
# ---------------------------------------------------------------------------

def refresh_clients_channels():
    """Rebuild the clients + channels display from live server state."""
    server = STATE.server

    clients_child = _TAG + ".clients"
    channels_child = _TAG + ".channels"

    for child in (clients_child, channels_child):
        dpg.delete_item(child, children_only=True)

    if server is None:
        dpg.add_text("(server not running)", parent=clients_child)
        dpg.add_text("(server not running)", parent=channels_child)
        return

    # Snapshot shared state under the server's lock.
    with server._lock:
        clients = {}
        for sock, client in list(server._clients.items()):
            nick = client.nick or "<unnamed>"
            addr = getattr(client, "addr", ("?",))
            addr_str = "%s:%s" % (addr[0], addr[1]) if len(addr) >= 2 else str(addr)
            clients[nick] = addr_str

        channels = {}
        for name, members in sorted(server._channels.items()):
            channels[name] = sorted(members.keys())

    # Render clients.
    if not clients:
        dpg.add_text("(no clients connected)", parent=clients_child)
    else:
        for nick in sorted(clients):
            dpg.add_text("%s   @ %s" % (nick, clients[nick]), parent=clients_child)

    # Render channels.
    if not channels:
        dpg.add_text("(no channels)", parent=channels_child)
    else:
        for name, members in channels.items():
            member_str = ", ".join(members) if members else "(empty)"
            dpg.add_text("%s: %s" % (name, member_str), parent=channels_child)


def on_refresh(sender, app_data, user_data):
    refresh_clients_channels()


# ---------------------------------------------------------------------------
# Periodic tick (tail log + optional auto refresh)
# ---------------------------------------------------------------------------

# How often (seconds) the render loop runs background work.
TICK_INTERVAL = 0.5
STATUS_REFRESH_INTERVAL = 2.0  # seconds between client/channel panel refreshes


def on_tick():
    """Periodic callback: tail the log and auto-refresh the status panel."""
    _tail_log()

    # Auto-refresh clients/channels every ~2 seconds using a reliable timer
    # (the previous modulo-time approach only fired in narrow windows).
    now = time.time()
    if now - STATE.last_status_refresh >= STATUS_REFRESH_INTERVAL:
        STATE.last_status_refresh = now
        refresh_clients_channels()


# ---------------------------------------------------------------------------
# UI construction
# ---------------------------------------------------------------------------

def build_ui():
    """Create the full dearpygui window/layout and register callbacks."""
    with dpg.window(
        label="Agent IRC Server Launcher",
        tag=_TAG + ".window",
        width=900,
        height=700,
    ):
        dpg.add_text("Bind host/port and manage the IRC server.")

        # --- Connection controls ---
        with dpg.group(horizontal=True):
            dpg.add_text("Host:")
            dpg.add_input_text(default_value=DEFAULT_HOST, tag=_TAG + ".host",
                               width=140)
            dpg.add_text("Port:")
            dpg.add_input_int(default_value=DEFAULT_PORT, tag=_TAG + ".port",
                              width=90)
            dpg.add_text("Log path:")
            dpg.add_input_text(default_value=DEFAULT_LOG_PATH,
                               tag=_TAG + ".log_path", width=320)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Start", callback=on_start, tag=_TAG + ".start")
            dpg.add_button(label="Stop", callback=on_stop, tag=_TAG + ".stop")
            dpg.configure_item(_TAG + ".stop", enabled=False)
            dpg.add_button(label="Refresh status", callback=on_refresh)

        dpg.add_separator()

        # --- Observability panels ---
        with dpg.collapsing_header(label="Server Log (live JSONL tail)",
                                   default_open=True):
            with dpg.child_window(tag=_TAG + ".log_container", height=320,
                                  border=True):
                with dpg.group(tag=_TAG + ".log_text"):
                    pass

        with dpg.collapsing_header(label="Clients & Channels", default_open=True):
            with dpg.group(horizontal=True):
                with dpg.child_window(label="", tag=_TAG + ".clients_win",
                                      width=420, height=160, border=True):
                    dpg.add_text("Clients:", bullet=False)
                    dpg.add_group(tag=_TAG + ".clients")
                with dpg.child_window(label="", tag=_TAG + ".channels_win",
                                      width=420, height=160, border=True):
                    dpg.add_text("Channels:", bullet=False)
                    dpg.add_group(tag=_TAG + ".channels")

    # Initial status populate.
    refresh_clients_channels()
    ui_log("Launcher ready.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Set up dearpygui, build the UI, and enter the render loop."""
    # Open the launcher log file for appending (best-effort).
    try:
        STATE.launcher_log_fh = open(_LAUNCHER_LOG_PATH, "a", encoding="utf-8")
    except OSError:
        STATE.launcher_log_fh = None

    dpg.create_context()
    try:
        build_ui()
        dpg.create_viewport(title="Agent IRC Server Launcher",
                            width=940, height=740)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Drive the UI with a periodic tick so we can tail the log off the
        # blocking render loop while keeping the server on its own thread.
        while dpg.is_dearpygui_running():
            on_tick()
            dpg.render_dearpygui_frame()
    finally:
        if STATE.server is not None:
            try:
                STATE.server._shutdown()
            except Exception:  # noqa: BLE001
                pass
            STATE.server = None
            STATE.thread = None
        if STATE.launcher_log_fh is not None:
            STATE.launcher_log_fh.close()
            STATE.launcher_log_fh = None
        dpg.destroy_context()


if __name__ == "__main__":
    main()

