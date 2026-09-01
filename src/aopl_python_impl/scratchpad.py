# aopl_python_impl/scratchpad.py
#
# Console-script entry for Cosmic Scratchpad.
from __future__ import annotations

import sys


def main() -> None:
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except ImportError:
        print(
            "Cosmic Scratchpad needs the GUI extra.\n"
            "  pip install -e \".[gui]\"\n"
            "or: pip install -e \".[all]\"",
            file=sys.stderr,
        )
        sys.exit(1)

    from aopl_python_impl.gui.app import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
