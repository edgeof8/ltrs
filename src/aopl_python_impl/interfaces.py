# aopl_python_impl/interfaces.py

from typing import Callable, Dict
from .definitions import ValueTuple

TermGetter = Callable[[str, Dict[str, ValueTuple], str], ValueTuple]
