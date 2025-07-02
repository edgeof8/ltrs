# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional, Any
import logging

# --- IMPORT THE RUST CORE ---
try:
    import importlib
    rust_core = importlib.import_module(".aop_rust_core", package="aopl_python_impl")
    _RUST_CORE_ENABLED = True
    logging.info("Rust core loaded successfully.")
except ImportError as e:
    _RUST_CORE_ENABLED = False
    logging.warning(f"Could not load Rust core: {e}. Falling back to Python implementation.")

# This Python class is now a direct, simple wrapper around the Rust implementation.
# The Rust code is now considered the source of truth.
class AoPValue:
    _rust_obj: Any

    def __init__(self, poly: Optional[Dict[str, int]] = None, base: int = 10, is_negative: bool = False):
        if not _RUST_CORE_ENABLED:
            raise RuntimeError("Rust core is not enabled.")
        # The __init__ directly calls the Rust constructor. PyO3 handles the wrapping.
        self._rust_obj = rust_core.AoPValue(poly, base, is_negative)

    @classmethod
    def from_number(cls, n: int, base: int = 10) -> 'AoPValue':
        if not _RUST_CORE_ENABLED:
            raise RuntimeError("Rust core is not enabled.")
        # Create an empty shell and assign the object returned by the Rust static method.
        instance = cls.__new__(cls)
        instance._rust_obj = rust_core.AoPValue.from_number(n, base)
        return instance

    @staticmethod
    def _wrap_rust_result(rust_obj: Any) -> 'AoPValue':
        """A helper to wrap a raw rust object in a new Python AoPValue instance."""
        # Create a new, empty instance of this Python wrapper class
        instance = AoPValue.__new__(AoPValue)
        # Place the raw Rust object inside it
        instance._rust_obj = rust_obj
        return instance

    @property
    def poly(self) -> Dict[str, int]:
        return self._rust_obj.poly

    @property
    def base(self) -> int:
        return self._rust_obj.base

    @property
    def is_negative(self) -> bool:
        return self._rust_obj.is_negative

    def to_numerical(self) -> int:
        return self._rust_obj.to_numerical()

    # The dunder methods simply delegate to the Rust implementation.
    # The key is to unwrap the `other` argument and re-wrap the result.
    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue):
            return NotImplemented
        result_rust_obj = self._rust_obj.__add__(other._rust_obj)
        return self._wrap_rust_result(result_rust_obj)

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue):
            return NotImplemented
        result_rust_obj = self._rust_obj.__sub__(other._rust_obj)
        return self._wrap_rust_result(result_rust_obj)

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue):
            return NotImplemented
        result_rust_obj = self._rust_obj.__mul__(other._rust_obj)
        return self._wrap_rust_result(result_rust_obj)

    def __pow__(self, other: 'AoPValue', modulo: Optional[Any] = None) -> 'AoPValue':
        if not isinstance(other, AoPValue):
            return NotImplemented
        # The Rust __pow__ is fallible, so PyO3 will raise an exception on error.
        result_rust_obj = self._rust_obj.__pow__(other._rust_obj, modulo)
        return self._wrap_rust_result(result_rust_obj)

    def __iadd__(self, other: 'AoPValue') -> 'AoPValue':
        """Implements in-place addition (e.g., a += b)."""
        if not isinstance(other, AoPValue):
            return NotImplemented
        # Rust's __add__ is not in-place, so we call it and re-assign the result.
        new_rust_obj = self._rust_obj.__add__(other._rust_obj)
        self._rust_obj = new_rust_obj
        return self

    def __repr__(self) -> str:
        return self._rust_obj.__repr__()

    def __reduce__(self):
        """Tells Python's pickle module how to serialize this object."""
        return (AoPValue, (self.poly, self.base, self.is_negative))
