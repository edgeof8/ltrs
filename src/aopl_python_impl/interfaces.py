# aopl_python_impl/interfaces.py

from __future__ import annotations
# FIX: Import TYPE_CHECKING from the typing module
from typing import Callable, Dict, TYPE_CHECKING

# This 'if' block is a special construct. The code inside it is ONLY
# processed by static type checkers (like Pylance). It is NEVER run
# by the Python interpreter. This lets us safely import AoPValue for
# type analysis without causing a circular import at runtime.
if TYPE_CHECKING:
    from .aop_value import AoPValue

# Now, when Pylance sees the string 'AoPValue', it will look inside the
# TYPE_CHECKING block to understand what it means, and the error will be resolved.
TermGetter = Callable[[str, Dict[str, 'AoPValue'], str], 'AoPValue']
