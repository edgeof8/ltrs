# aopl_python_impl/interfaces.py

from __future__ import annotations
from typing import Callable, Dict, TYPE_CHECKING

# This 'if' block is a special construct. The code inside it is ONLY
# processed by static type checkers (like Pylance). It is NEVER run
# by the Python interpreter. This lets us safely import AoPValue for
# type analysis without causing a circular import error at runtime.
if TYPE_CHECKING:
    from .aop_value import AoPValue

# Defines a type hint for a callable that gets a term.
TermGetter = Callable[[str, Dict[str, 'AoPValue'], str], 'AoPValue']
