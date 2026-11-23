"""Kill orphaned agent IRC server processes and free their ports.

Sometimes a server (started via `run_server.py` or the launcher) is left
running after its terminal/UI is closed, leaving the port bound and blocking
new instances. This script finds such processes and terminates them.

Usage:
    python kill_server.py                 # kill processes named like the server
    python kill_server.py --port 6667     # additionally free a specific port
    python kill_server.py --all           # kill every matching server process
    python kill_server.py --dry-run       # show what would be killed, don't kill

It works on Linux/macOS (psutil-free: uses /proc or `ps`) and gives a clear
list of anything it kills. It does NOT require the server to be imported.
"""

import argparse
import os
import signal
import subprocess
import sys

# Names we consider "an agent IRC server process".
SERVER_MARKERS = ("run_server.py", "irc_server.py", "launcher.py")


def _is_server_cmdline(cmdline):
    """Return True if the process command line looks like our server."""
    joined = " ".join(cmdline)
    return any(m in joined for m in SERVER_MARKERS) and "python" in joined.lower()


def _list_processes():
    """Yield (pid, cmdline) for candidate python processes, cross-platform."""
    # Linux: /proc.
    if os.path.isdir("/proc"):
        try:
            for pid in os.listdir("/proc"):
                if not pid.isdigit():
                    continue
                cmd_path = "/proc/%s/cmdline" % pid
                try:
                    with open(cmd_path, "rb") as fh:
                        raw = fh.read().replace(b"\x00", b" ").decode("utf-8", "replace")
                    cmdline = raw.split()
                    if cmdline:
                        yield int(pid), cmdline
                except (OSError, IOError):
                    continue
        except OSError:
            pass
    # Fallback: ps.
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,args"], text=True)
        for line in out.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            pid_s, _, args = line.partition(" ")
            pid_s = pid_s.strip()
            if not pid_s.isdigit():
                continue
            yield int(pid_s), args.split()
    except (OSError, subprocess.SubprocessError):
        pass


def _port_holders(port):
    """Find PIDs listening on `port` using `lsof`/`ss` (best effort)."""
    pids = set()
    for cmd in (
        ["lsof", "-ti", "tcp:%d" % port],
        ["lsof", "-t", "-i", "tcp:%d" % port],
        ["ss", "-tlnp"],
    ):
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            for tok in out.split():
                if tok.isdigit():
                    pids.add(int(tok))
        except (OSError, subprocess.SubprocessError):
            continue
    return pids


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=None,
                        help="also find/kill anything holding this TCP port")
    parser.add_argument("--all", action="store_true",
                        help="kill every matching server process (no confirmation)")
    parser.add_argument("--dry-run", action="store_true",
                        help="list what would be killed without killing")
    args = parser.parse_args(argv)

    targets = {}  # pid -> cmdline

    # 1) Processes whose cmdline matches our server names.
    for pid, cmdline in _list_processes():
        if pid == os.getpid():
            continue
        if _is_server_cmdline(cmdline):
            targets[pid] = cmdline

    # 2) Processes holding the requested port.
    if args.port is not None:
        for pid in _port_holders(args.port):
            if pid != os.getpid() and pid not in targets:
                targets[pid] = ["<port %d holder>" % args.port]

    if not targets:
        print("No orphaned server processes found.")
        return 0

    print("Found %d candidate process(es):" % len(targets))
    for pid, cmdline in sorted(targets.items()):
        print("  PID %d: %s" % (pid, " ".join(cmdline)))

    if args.dry_run:
        print("--dry-run: nothing killed.")
        return 0

    if not args.all:
        try:
            ans = input("Kill these processes? [y/N] ").strip().lower()
        except EOFError:
            ans = "n"
        if ans != "y":
            print("Aborted.")
            return 0

    killed = 0
    for pid in sorted(targets):
        try:
            os.kill(pid, signal.SIGTERM)
            print("  sent SIGTERM to %d" % pid)
            killed += 1
        except (ProcessLookupError, PermissionError) as exc:
            print("  could not kill %d: %s" % (pid, exc))

    print("Signal sent to %d process(es). Use --port to verify the port is free." % killed)
    return 0


if __name__ == "__main__":
    sys.exit(main())

