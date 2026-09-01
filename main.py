"""Launch Cosmic Scratchpad from a repository checkout."""
from pathlib import Path
import sys

_src = Path(__file__).resolve().parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from aopl_python_impl.scratchpad import main

if __name__ == "__main__":
    main()
