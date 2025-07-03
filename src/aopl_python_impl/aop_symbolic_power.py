# aopl_python_impl/aop_symbolic_power.py
from __future__ import annotations
from typing import Dict, Union
from .aop_value import AoPValue
from .definitions import int_to_key, key_to_int
from .aop_logger import log_pow

class SymbolicPower:
    def __init__(self, base: Union['AoPValue', 'SymbolicPower'], exponent: Union['AoPValue', 'SymbolicPower']):
        self.base = base
        self.exponent = exponent

    def __repr__(self) -> str:
        return f"SymbolicPower({self.base!r}^{self.exponent!r})"
