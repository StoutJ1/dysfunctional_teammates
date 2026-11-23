"""Quick start: run the agent IRC server (headless, no GUI).

Usage:
    python run_server.py --host 127.0.0.1 --port 6667 --log irc_server.log
"""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from server.irc_server import main

if __name__ == "__main__":
    main()

