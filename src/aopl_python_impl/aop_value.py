# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional, Any, TYPE_CHECKING
import logging
from .definitions import LETTER_TO_EXPONENT_MAP
import re

if TYPE_CHECKING:
    from . import aop_rust_core as rust_core

try:
    from . import aop_rust_core as rust_core
    _RUST_CORE_ENABLED = True
    logging.info("Rust core loaded successfully.")
except ImportError as e:
    _RUST_CORE_ENABLED = False
    rust_core = None
    logging.warning(f"Could not load Rust core: {e}. Falling back to Python implementation.")

class AoPValue:
    _rust_obj: Any

    # Private constructor for internal wrapping
    def __init__(self, rust_obj=None):
        if not rust_core:
            raise RuntimeError("Rust core is not enabled.")
        if rust_obj:
            self._rust_obj = rust_obj
        else:
            # Create a default empty rust object
            self._rust_obj = rust_core.AoPValue()

    @classmethod
    def from_literal(cls, literal_str: str, base: int = 10) -> 'AoPValue':
        if not rust_core: raise RuntimeError("Rust core not loaded.")
        # Call the Rust static method
        rust_obj = rust_core.AoPValue.from_literal(literal_str, base)
        # Wrap the returned Rust object in our Python class
        return cls(rust_obj=rust_obj)

    @classmethod
    def from_number(cls, n: int, base: int = 10) -> 'AoPValue':
        if not rust_core: raise RuntimeError("Rust core not loaded.")
        rust_obj = rust_core.AoPValue.from_number(n, base)
        return cls(rust_obj=rust_obj)

    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        result_rust_obj = self._rust_obj.__add__(other._rust_obj)
        return AoPValue(rust_obj=result_rust_obj)

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        result_rust_obj = self._rust_obj.__sub__(other._rust_obj)
        return AoPValue(rust_obj=result_rust_obj)

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        result_rust_obj = self._rust_obj.__mul__(other._rust_obj)
        return AoPValue(rust_obj=result_rust_obj)

    def __pow__(self, other: 'AoPValue') -> 'AoPValue':
        result_rust_obj = self._rust_obj.power(other._rust_obj)
        return AoPValue(rust_obj=result_rust_obj)

    def to_numerical(self) -> int:
        return self._rust_obj.to_numerical()

    def __str__(self) -> str:
        return self._rust_obj.__str__()

    def __repr__(self) -> str:
        return self._rust_obj.__repr__()

    # Delegate attribute access to the underlying rust object
    def __getattr__(self, name):
        return getattr(self._rust_obj, name)

    # Pickle support
    def __getstate__(self):
        return self._rust_obj.__getstate__()

    def __setstate__(self, state):
        if not hasattr(self, '_rust_obj'):
            self._rust_obj = rust_core.AoPValue()
        self._rust_obj.__setstate__(state)
