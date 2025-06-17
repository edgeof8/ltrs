# aopl_python_impl/interfaces.py

from typing import Callable, Dict
from .aop_value import AoPValue # <-- Import the new class

# Update the return type from ValueTuple to AoPValue
TermGetter = Callable[[str, Dict[str, AoPValue], str], AoPValue]
