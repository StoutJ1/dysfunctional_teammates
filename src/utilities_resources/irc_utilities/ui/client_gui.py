"""Agent IRC Client GUI — a dearpygui chat client.

Connects to the agent IRC server (newline-delimited JSON protocol) using the
supplied ``AgentIRCClient`` library.  Provides:

  * host / port / nickname inputs and Connect / Disconnect buttons.
  * a channel input and Join / Part buttons.
  * a scrolling message log (PRIVMSG/NICK/JOIN/PART events plus errors).
  * a text input + Send button to chat in the current channel.
  * a per-frame ``poll()`` of the client so the log always stays live without
    ever blocking the UI thread.

Membership is tracked from server replies so the Send box is only enabled
after the server actually confirms a JOIN (no more "not in channel" races).

Run directly::

    python client_gui.py

Or import and call ``main()``.
"""

import os
import sys
import time

import dearpygui.dearpygui as dpg

# Make sure the sibling client library is importable regardless of how this
# file is executed.  ``parent/client`` is v<N>/client (works from v2 too).
_HERE = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_HERE)  # v2/ or v1/
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from client.agent_irc_client import AgentIRCClient  # noqa: E402

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6667
DEFAULT_NICK = "gui-user"
DEFAULT_CHANNEL = "#general"

# Tag namespace prefix to avoid collisions with other windows.
_TAG = "agent_irc_client"

# Maximum lines retained in the in-memory log (keep the UI responsive).
MAX_LOG_LINES = 2000


class ChatState(object):
    """Holds the live client instance and the chat log buffer."""

    def __init__(self):
        self.client = None          # AgentIRCClient or None when disconnected
        self.log_lines = []         # list of formatted log strings
        self.current_channel = ""   # channel we are ACTUALLY joined to
        self.joined = False         # True once server confirms JOIN
        self.nickname = DEFAULT_NICK


STATE = ChatState()


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log(line):
    """Append a line to the in-memory log and refresh the visible text."""
    STATE.log_lines.append(line)
    # Bound the log so the UI never grinds to a halt.
    if len(STATE.log_lines) > MAX_LOG_LINES:
        STATE.log_lines = STATE.log_lines[-MAX_LOG_LINES:]
    _refresh_log()


def _refresh_log():
    """Push the current log buffer into the dearpygui text widget and scroll
    to the bottom so the newest message is always visible."""
    if not dpg.does_item_exist(_TAG + ".log_text"):
        return
    dpg.set_value(_TAG + ".log_text", "\n".join(STATE.log_lines) + "\n")
    # Auto-scroll the child window to the very bottom on every refresh.
    if dpg.does_item_exist(_TAG + ".log_container"):
        dpg.set_y_scroll(_TAG + ".log_container", -1.0)


def _clear_log():
    STATE.log_lines = []
    _refresh_log()


def _ts():
    return time.strftime("%H:%M:%S")


# ---------------------------------------------------------------------------
# Event formatting (server event dicts -> readable chat lines)
# ---------------------------------------------------------------------------

def _format_event(msg):
    """Turn a single ``poll()`` dict into a display string.

    Handles:
      * ``event`` messages (PRIVMSG / JOIN / PART / NICK),
      * ``reply`` messages (LIST / HISTORY / JOIN ...),
      * ``error`` messages.
    """
    mtype = msg.get("type")

    if mtype == "event":
        event = msg.get("event")
        nick = msg.get("nick")
        channel = msg.get("channel")
        if event == "PRIVMSG":
            where = "(%s)" % channel if channel else ""
            return "[%s] %s%s: %s" % (_ts(), nick, where, msg.get("text", ""))
        if event == "JOIN":
            return "[%s] * %s has joined %s" % (_ts(), nick, channel)
        if event == "PART":
            return "[%s] * %s has left %s" % (_ts(), nick, channel)
        if event == "NICK":
            return "[%s] * %s is now known as %s" % (
                _ts(), nick, msg.get("new_nick", msg.get("nick")))
        # Fallback: dump the raw event dict.
        return "[%s] %s %r" % (_ts(), event, msg)

    if mtype == "reply":
        cmd = msg.get("cmd")
        if cmd == "JOIN":
            members = msg.get("members", [])
            return "[%s] Joined %s (%d member(s): %s)" % (
                _ts(), msg.get("channel", "?"),
                len(members), ", ".join(members))
        if cmd == "LIST":
            channels = msg.get("channels", [])
            names = []
            for ch in channels:
                members = ch.get("members", [])
                names.append("%s(%d)" % (ch.get("channel", "?"), len(members)))
            return "[%s] Channels: %s" % (_ts(), ", ".join(names) or "(none)")
        if cmd == "HISTORY":
            msgs = msg.get("messages", [])
            if not msgs:
                return "[%s] (no history)" % _ts()
            lines = []
            for m in msgs:
                lines.append("[%s] <%s> %s" % (
                    time.strftime("%H:%M:%S", time.localtime(m.get("ts", 0))),
                    m.get("nick", "?"), m.get("text", "")))
            return "[%s] --- history ---\n%s" % (_ts(), "\n".join(lines))
        return "[%s] reply %s: %r" % (_ts(), cmd, msg)

    if mtype == "error":
        return "[%s] ERROR: %s" % (_ts(), msg.get("error", msg))

    # Unknown shape; show it raw but readable.
    return "[%s] %r" % (_ts(), msg)


# ---------------------------------------------------------------------------
# Control enable/disable helpers
# ---------------------------------------------------------------------------

def _set_input_enabled(enabled):
    """Enable/disable the Send button and message input together."""
    dpg.configure_item(_TAG + ".send", enabled=enabled)
    dpg.configure_item(_TAG + ".input", enabled=enabled)


def _focus_input():
    """(Re)give keyboard focus to the message input, if it is enabled."""
    try:
        if dpg.does_item_exist(_TAG + ".input"):
            dpg.focus_item(_TAG + ".input")
    except Exception:  # noqa: BLE001 - focus is best-effort only
        pass




def _normalize_channel(name):
    """Coerce a user-typed channel to a canonical '#name' form.

    Users often type a channel without the leading '#' (e.g. "general" or
    "randomroom"); the server accepts either, but they become different
    channels. Normalizing here keeps "make up a channel" intuitive.
    """
    name = (name or "").strip()
    if not name:
        return ""
    return name if name.startswith("#") else "#" + name

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def on_connect(sender, app_data, user_data):
    """Open a connection; on success enable the channel controls."""
    if STATE.client is not None:
        log("Already connected. Disconnect first.")
        return

    host = (dpg.get_value(_TAG + ".host") or "").strip() or DEFAULT_HOST
    try:
        port = int(dpg.get_value(_TAG + ".port"))
    except (ValueError, TypeError):
        port = DEFAULT_PORT
    nick = (dpg.get_value(_TAG + ".nick") or "").strip() or DEFAULT_NICK

    client = AgentIRCClient()
    try:
        client.connect(host, port, nick)
    except OSError as exc:
        log("Connection failed: %s" % exc)
        return

    STATE.client = client
    STATE.nickname = nick
    STATE.joined = False
    STATE.current_channel = ""
    log("Connected to %s:%d as %s" % (host, port, nick))

    dpg.configure_item(_TAG + ".connect", enabled=False)
    dpg.configure_item(_TAG + ".disconnect", enabled=True)
    dpg.configure_item(_TAG + ".join", enabled=True)
    dpg.configure_item(_TAG + ".part", enabled=False)
    # Send stays disabled until the server confirms a JOIN.
    _set_input_enabled(False)


def on_disconnect(sender, app_data, user_data):
    """Politely disconnect and reset controls."""
    client = STATE.client
    if client is not None:
        try:
            client.quit()
        except (OSError, ValueError):
            pass
        log("Disconnected.")
        STATE.client = None
    STATE.joined = False
    STATE.current_channel = ""

    dpg.configure_item(_TAG + ".connect", enabled=True)
    dpg.configure_item(_TAG + ".disconnect", enabled=False)
    dpg.configure_item(_TAG + ".join", enabled=False)
    dpg.configure_item(_TAG + ".part", enabled=False)
    _set_input_enabled(False)


def on_join(sender, app_data, user_data):
    """Send a JOIN for the channel named in the channel input.

    We do *not* enable Send yet — that happens only when the server's JOIN
    reply confirms membership (see ``on_tick``).
    """
    client = STATE.client
    if client is None:
        log("Not connected.")
        return

    channel = _normalize_channel(dpg.get_value(_TAG + ".channel"))
    if not channel:
        log("Enter a channel name first.")
        return

    client.join(channel)
    log("Joining %s ..." % channel)


def on_part(sender, app_data, user_data):
    """Leave the current channel."""
    client = STATE.client
    if client is None:
        return

    channel = STATE.current_channel
    if not channel:
        return
    client.part(channel)
    log("Left %s." % channel)
    STATE.joined = False
    STATE.current_channel = ""

    dpg.configure_item(_TAG + ".join", enabled=True)
    dpg.configure_item(_TAG + ".part", enabled=False)
    _set_input_enabled(False)


def on_send(sender, app_data, user_data):
    """Send the message text to the current channel."""
    _send_current_input()


def _send_current_input():
    client = STATE.client
    if client is None:
        log("Not connected.")
        return

    if not STATE.joined or not STATE.current_channel:
        log("You are not in a channel yet. Join one first.")
        return

    text = (dpg.get_value(_TAG + ".input") or "").strip()
    if not text:
        return

    try:
        client.send(STATE.current_channel, text)
    except (OSError, ValueError) as exc:
        log("Send failed: %s" % exc)
        return

    # Clear the input and keep focus so the user can keep typing.
    dpg.set_value(_TAG + ".input", "")
    _focus_input()


def on_input_enter(sender, app_data, user_data):
    """Send when the user presses Enter inside the message box."""
    _send_current_input()


# ---------------------------------------------------------------------------
# Periodic tick: poll the client and render new events
# ---------------------------------------------------------------------------

def on_tick():
    """Non-blocking poll; called once per render frame."""
    client = STATE.client
    if client is None:
        return

    try:
        msgs = client.poll()
    except Exception as exc:  # noqa: BLE001 - never let a poll break the UI
        log("Poll error: %s" % exc)
        return

    for msg in msgs:
        _handle_message(msg)


def _handle_message(msg):
    """Update state for a single polled message, then render it."""
    mtype = msg.get("type")

    # --- JOIN reply confirms we are actually a member now ---
    if mtype == "reply" and msg.get("cmd") == "JOIN":
        channel = msg.get("channel", "")
        STATE.current_channel = channel
        STATE.joined = True
        dpg.configure_item(_TAG + ".join", enabled=False)
        dpg.configure_item(_TAG + ".part", enabled=True)
        _set_input_enabled(True)
        _focus_input()

    # --- PART event: if it's us leaving, reset membership ---
    if mtype == "event" and msg.get("event") == "PART":
        nick = msg.get("nick")
        if nick == STATE.nickname or msg.get("channel") == STATE.current_channel:
            # Only treat our own PART as ending membership.  A PART for our
            # channel from another nick shouldn't disable our box, but if the
            # server echoed OUR part it will carry our nick.
            if nick == STATE.nickname:
                STATE.joined = False
                STATE.current_channel = ""
                dpg.configure_item(_TAG + ".join", enabled=True)
                dpg.configure_item(_TAG + ".part", enabled=False)
                _set_input_enabled(False)

    # --- Server-initiated disconnect (socket closed) ---
    if mtype == "error" and "closed" in str(msg.get("error", "")).lower():
        log(_format_event(msg))
        on_disconnect(None, None, None)
        return

    log(_format_event(msg))


# ---------------------------------------------------------------------------
# UI construction
# ---------------------------------------------------------------------------

def build_ui():
    """Create the client window and register all callbacks/controls."""
    with dpg.window(
        label="Agent IRC Client",
        tag=_TAG + ".window",
        width=-1,
        height=-1,
        no_scrollbar=True,
    ):
        dpg.add_text("Connect to a server and chat in a channel.")

        # --- Connection controls ---
        with dpg.group(horizontal=True):
            dpg.add_text("Host:")
            dpg.add_input_text(default_value=DEFAULT_HOST, tag=_TAG + ".host",
                               width=-1)
            dpg.add_text("Port:")
            dpg.add_input_int(default_value=DEFAULT_PORT, tag=_TAG + ".port",
                              width=100)
            dpg.add_text("Nick:")
            dpg.add_input_text(default_value=DEFAULT_NICK, tag=_TAG + ".nick",
                               width=-1)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Connect", callback=on_connect,
                           tag=_TAG + ".connect")
            dpg.add_button(label="Disconnect", callback=on_disconnect,
                           tag=_TAG + ".disconnect")
            dpg.configure_item(_TAG + ".disconnect", enabled=False)

        dpg.add_separator()

        # --- Channel controls ---
        with dpg.group(horizontal=True):
            dpg.add_text("Channel:")
            dpg.add_input_text(default_value=DEFAULT_CHANNEL,
                               tag=_TAG + ".channel", width=-1)
            dpg.add_button(label="Join", callback=on_join, tag=_TAG + ".join")
            dpg.add_button(label="Part", callback=on_part, tag=_TAG + ".part")

        dpg.add_separator()

        # --- Scrolling message log (stretches to fill remaining space) ---
        with dpg.child_window(tag=_TAG + ".log_container", border=True,
                              horizontal_scrollbar=True, height=-1):
            dpg.add_text("", tag=_TAG + ".log_text", wrap=0)

        dpg.add_separator()

        # --- Message input + Send ---
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag=_TAG + ".input",
                hint="Join a channel first, then type here",
                width=-1,
                callback=on_input_enter,
                on_enter=True,
            )
            dpg.add_button(label="Send", callback=on_send, tag=_TAG + ".send")

        dpg.add_button(label="Clear log", callback=_clear_log)

    # Start with chat controls disabled (nothing connected yet).
    dpg.configure_item(_TAG + ".join", enabled=False)
    dpg.configure_item(_TAG + ".part", enabled=False)
    _set_input_enabled(False)

    log("Welcome to the Agent IRC Client!")
    log("How to get started:")
    log("  1. Enter host/port/nick and click Connect.")
    log("  2. Type a channel (e.g. #general) and click Join.")
    log("  3. Once joined, type a message below and press Enter.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Set up dearpygui, build the UI, and enter the render loop."""
    dpg.create_context()
    try:
        build_ui()
        dpg.set_primary_window(_TAG + ".window", True)
        dpg.create_viewport(title="Agent IRC Client", width=760, height=620,
                            resizable=True)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Drive the UI manually so we can poll the IRC client every frame.
        while dpg.is_dearpygui_running():
            on_tick()
            dpg.render_dearpygui_frame()
    finally:
        # Best-effort cleanup on exit.
        if STATE.client is not None:
            try:
                STATE.client.quit()
            except (OSError, ValueError):
                pass
            STATE.client = None
        dpg.destroy_context()


if __name__ == "__main__":
    main()

