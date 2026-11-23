import json
import os
import sys
from utilities_resources.irc_utilities.client.agent_irc_client import AgentIRCClient  # noqa: E402

_BASE = os.path.dirname(os.path.abspath(__file__))


def _find_client_dir():
    d = _BASE
    for _ in range(8):
        candidate = os.path.join(d, "utilities_resources","irc_utilities", "client")
        if os.path.isfile(os.path.join(candidate, "agent_irc_client.py")):
            return candidate
        else:
            print("Failed to get IRC client file.")

_CLIENT_DIR = _find_client_dir()



def irc_connect_schema():
    return {
        "type": "function",
        "name": "irc_connect",
        "description": "Connect an IRC agent client to the v2 server and register a nickname.",
        "parameters": {
            "type": "object",
            "properties": {
                "nickname": {"type": "string", "description": "Nickname to register as"},
            },
            "required": ["nickname"],
        },
        "strict": True,
    }


def irc_send_schema():
    return {
        "type": "function",
        "name": "irc_send",
        "description": "Send a message to an IRC channel via a previously connected client.",
        "parameters": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel name, e.g. #general"},
                "message": {"type": "string", "description": "Text to send"},
            },
            "required": ["channel", "message"],
        },
        "strict": True,
    }


def irc_join_schema():
    return {
        "type": "function",
        "name": "irc_join",
        "description": "Join an IRC channel.",
        "parameters": {
            "type": "object",
            "properties": {"channel": {"type": "string", "description": "Channel name"}},
            "required": ["channel"],
        },
        "strict": True,
    }


def irc_poll_schema():
    return {
        "type": "function",
        "name": "irc_poll",
        "description": "Return messages received since the last poll on the shared client.",
        "parameters": {"type": "object", "properties": {}, "required": []},
        "strict": True,
    }


def irc_list_channels_schema():
    return {
        "type": "function",
        "name": "irc_list_channels",
        "description": "List channels and their members from the connected server.",
        "parameters": {"type": "object", "properties": {}, "required": []},
        "strict": True,
    }


def irc_history_schema():
    return {
        "type": "function",
        "name": "irc_history",
        "description": "Get the most recent messages for a channel. Include the #",
        "parameters": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel name"},
                "n": {"type": "integer", "description": "Number of messages to return (default 50)"},
            },
            "required": ["channel"],
        },
        "strict": True,
    }


_clients = {}          # nickname -> AgentIRCClient
_default_nick = None   # nickname of the most recently connected client


def _get_client(nickname=None):
    key = nickname or _default_nick
    if key is None:
        raise ValueError("no IRC client connected; call irc_connect(nickname) first")
    c = _clients.get(key)
    if c is None:
        raise ValueError("no IRC client connected as %r" % (key,))
    return c


def irc_connect(working_directory="", nickname=None, host="127.0.0.1", port=6667):
    global _default_nick
    if not nickname:
        raise ValueError("nickname is required")
    # Reconnect cleanly if this nickname is already connected.
    old = _clients.get(nickname)
    if old is not None:
        try:
            old.quit()
        except Exception:
            pass
    c = AgentIRCClient()
    c.connect(host, int(port), nickname)
    c.join("#general")
    _clients[nickname] = c
    _default_nick = nickname
    return "Connected as %s to %s:%d" % (nickname, host, int(port))


def irc_send(channel, message, working_directory="", nickname=None):
    c = _get_client(nickname)
    c.send(channel, message)
    return "sent"


def irc_join(channel, working_directory="", nickname=None):
    c = _get_client(nickname)
    c.join(channel)
    return "joined %s" % channel


def irc_poll(nickname=None):
    c = _get_client(nickname)
    return c.poll()


def irc_list_channels(nickname=None):
    c = _get_client(nickname)
    return c.list_channels()


def irc_history(working_directory="", channel="#general", n=50, nickname=None):
    c = _get_client(nickname)
    try:
        print("Getting IRC History ", "Number", n, " messages")
        return c.history(channel, n)
    except ValueError:
        return "Not Connected"


if __name__ == "__main__":
    print(json.dumps(irc_connect_schema(), indent=2))
    print(json.dumps(irc_send_schema(), indent=2))
    print(json.dumps(irc_join_schema(), indent=2))
    print(json.dumps(irc_poll_schema(), indent=2))
    print(json.dumps(irc_list_channels_schema(), indent=2))
    print(json.dumps(irc_history_schema(), indent=2))

