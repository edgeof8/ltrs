# aopl_python_impl/scratchpad.py
#
# Console-script entry for Cosmic Scratchpad. GUI modules live at the repo
# root (main.py, cosmic_scene.py, …) until they are packaged separately.
from __future__ import annotations

import sys
from pathlib import Path


def _find_checkout_root() -> Path | None:
    """Locate a git checkout that contains main.py and cosmic_scene.py."""
    candidates: list[Path] = []
    try:
        candidates.append(Path.cwd().resolve())
    except OSError:
        pass
    candidates.extend(Path(__file__).resolve().parents)
    seen: set[Path] = set()
    for start in candidates:
        for folder in (start, *start.parents):
            if folder in seen:
                continue
            seen.add(folder)
            if (folder / "main.py").is_file() and (folder / "cosmic_scene.py").is_file():
                return folder
    return None


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

    root = _find_checkout_root()
    if root is None:
        print(
            "Could not find Cosmic Scratchpad sources (main.py / cosmic_scene.py).\n"
            "Install from a clone of the repository:\n"
            "  pip install -e \".[gui]\"\n"
            "  cosmic-scratchpad",
            file=sys.stderr,
        )
        sys.exit(1)

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    import main as scratchpad_app

    scratchpad_app.main()


if __name__ == "__main__":
    main()
