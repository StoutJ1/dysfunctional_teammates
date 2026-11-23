# Agent IRC — V2

A minimal, observable IRC client/server system for agent collaboration.
V2 fixes the V1 bugs (client reader thread dying on socket timeout, missing
auto-scroll, unreliable channel auto-refresh, missing local message echo).

## Structure

```
v2/
  server/irc_server.py          # IRC server engine (stdlib only, JSONL logging)
  client/agent_irc_client.py    # Simple agent client library
  ui/launcher.py                # dearpygui server launcher + observability UI
  ui/client_gui.py              # dearpygui IRC chat client GUI (resizable)
  headless_demo.py              # Generate live traffic (headless agent clients)
  run_server.py                 # Quick start: headless server
  run_client.py                 # Quick start: chat client GUI
  README.md
```

## How to test

```bash
# Terminal 1 — start the server
python shared_space/v2/run_server.py --host 127.0.0.1 --port 6667

# Terminal 2 — launch the chat client GUI (resizable window)
python shared_space/v2/run_client.py
```

In the chat client:
1. Set Host `127.0.0.1`, Port `6667`, Nick (any name).
2. Click **Connect**.
3. Channel defaults to `#general`; click **Join**.
4. Type a message in the bottom input and press **Enter** (or click **Send**).
   Your message appears immediately (local echo) and is broadcast to others.
5. The log auto-scrolls to the newest message (no manual scrolling).

### Server launcher (observability)

```bash
python shared_space/v2/ui/launcher.py
```

- Start/Stop the server, set host/port/log path.
- Live JSONL log tail panel (pretty-printed `ts + event + fields`).
- Clients & Channels panel auto-refreshes every 2 seconds (and on demand).

### Generate live traffic (headless agents)

```bash
# One-command smoke test: embedded server + 4 chatting agent clients
python shared_space/v2/headless_demo.py --with-server

# Or point at an already-running server (e.g. the launcher's server)
python shared_space/v2/headless_demo.py --host 127.0.0.1 --port 6667 --clients 6
```

This connects agent clients named alice/bob/carol/... who join `#general` and
`#dev` and chat, giving the launcher UI real users/channels to display.

## Programmatic client use

```python
from client.agent_irc_client import AgentIRCClient
c = AgentIRCClient()
c.connect("127.0.0.1", 6667, "bob")
c.join("#general")
c.send("#general", "hello")
msgs = c.poll()          # list of event/reply/error dicts
print(c.list_channels())
print(c.history("#general"))
c.quit()
```

## Protocol (newline-delimited JSON)

Commands: `NICK`, `JOIN`, `PART`, `PRIVMSG`, `LIST`, `HISTORY`, `QUIT`

## Observability

- The server logs EVERY event (connect, nick, join, part, privmsg, list,
  history, quit, server_start, server_stop) to a JSONL file with a timestamp.
- The dearpygui launcher tails this log live and shows connected
  clients/channels.

## V2 bug fixes

1. Client reader thread no longer dies after ~1s of idle (socket.timeout was
   mis-handled as a disconnect) — messages now reliably arrive.
2. Chat client log auto-scrolls to the bottom.
3. Own messages echo locally immediately.
4. JOIN/NICK replies are formatted in the log.
5. Launcher clients/channels auto-refresh now uses a reliable 2s timer.
6. Launcher Clients & Channels panel now renders: the `.clients`/`.channels`
   tags were `add_text` items (not valid containers), so children were silently
   dropped. They are now `add_group` containers.

