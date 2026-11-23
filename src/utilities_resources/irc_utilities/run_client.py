"""Quick start: launch the dearpygui IRC client chat GUI."""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "ui"))

from ui.client_gui import main

if __name__ == "__main__":
    main()

