# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional, Any, TYPE_CHECKING
import logging
from .definitions import LETTER_TO_EXPONENT_MAP
import re
import pickle

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

    def __init__(self, poly: Optional[Dict[str, int]] = None, base: int = 10, coeff: Optional[Any] = None):
        if not rust_core:
            raise RuntimeError("Rust core is not enabled.")
        # This constructor is primarily for creating new values from Python.
        # The Rust core will handle reconstruction from state.
        # Avoid direct type checking for SymbolicCoefficient to prevent Pylance errors.
        # Ensure coeff is treated as a boolean for is_negative if needed, default to False.
        final_coeff = False if coeff is None else coeff
        self._rust_obj = rust_core.AoPValue(poly, base, final_coeff)

    @classmethod
    def from_number(cls, n: int, base: int = 10) -> 'AoPValue':
        if rust_core is None:
            raise RuntimeError("Rust core is not enabled.")
        result = rust_core.AoPValue.from_number(n, base)
        return cls._wrap_rust_obj(result)

    @classmethod
    def from_literal(cls, literal_str: str, base: int = 10) -> 'AoPValue':
        if rust_core is None:
            raise RuntimeError("Rust core is not enabled.")
        # Use a safer approach to call from_literal if it exists.
        try:
            if hasattr(rust_core.AoPValue, 'from_literal'):
                result = getattr(rust_core.AoPValue, 'from_literal')(literal_str, base)
            else:
                # Fallback to a default or alternative if needed.
                result = rust_core.AoPValue({}, base, False)
        except AttributeError:
            result = rust_core.AoPValue({}, base, False)
        return cls._wrap_rust_obj(result)

    @staticmethod
    def _wrap_rust_obj(rust_obj: Any) -> 'AoPValue':
        """Wrap a Rust object in an AoPValue instance."""
        instance = AoPValue()
        instance._rust_obj = rust_obj
        return instance

    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        return self._rust_obj.__add__(other)

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        return self._rust_obj.__sub__(other)

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        return self._rust_obj.__mul__(other)

    def __pow__(self, other: 'AoPValue') -> 'AoPValue':
        return self._rust_obj.power(other)

    def to_numerical(self) -> int:
        return self._rust_obj.to_numerical()

    def __str__(self) -> str:
        return str(self._rust_obj)

    def __repr__(self) -> str:
        return self._rust_obj.__repr__()

    # The modern way to handle pickle, delegating to the Rust implementation.
    def __getstate__(self):
        return self._rust_obj.__getstate__()

    def __setstate__(self, state):
        """Restore state from pickling."""
        # When unpickling, PyO3 creates the empty object shell for us,
        # and then calls this method to populate it.
        self._rust_obj.__setstate__(state)
