# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional, Any, TYPE_CHECKING
import logging
import logging, pickle, re
from .definitions import LETTER_TO_EXPONENT_MAP

# --- This block is for Pylance/MyPy's benefit, it doesn't run ---
if TYPE_CHECKING:
    from . import aop_rust_core as rust_core

# --- This is the actual runtime import ---
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

    def __init__(self, poly: Optional[Dict[str, int]] = None, base: int = 10, coeff: Optional[int] = None, _rust_obj: Any = None):
        if not rust_core:
            raise RuntimeError("Rust core is not enabled.")

        if _rust_obj is not None:
            self._rust_obj = _rust_obj
        else:
            final_coeff = coeff if coeff is not None else 1
            self._rust_obj = rust_core.AoPValue(poly, base, final_coeff)

    @classmethod
    def from_number(cls, n: int, base: int = 10) -> 'AoPValue':
        if not rust_core: raise RuntimeError("Rust core is not enabled.")
        return cls(_rust_obj=rust_core.AoPValue.from_number(n, base))

    @classmethod
    def from_literal(cls, literal_str: str, base: int = 10) -> 'AoPValue':
        poly = {}
        term_pattern = re.compile(r'(\d+)?([a-zA-Z])|(\d+)')
        matches = list(term_pattern.finditer(literal_str))

        if len(matches) == 1:
            match = matches[0]
            coeff_str, letter, _ = match.groups()
            if letter:
                main_coeff = int(coeff_str) if coeff_str else 1
                exp = LETTER_TO_EXPONENT_MAP.get(letter, 0)
                poly[str(exp)] = 1
                return cls(poly=poly, base=base, coeff=main_coeff)

        for match in matches:
            coeff_str, letter, standalone_num = match.groups()
            if letter:
                coeff_val = int(coeff_str) if coeff_str else 1
                exp = LETTER_TO_EXPONENT_MAP.get(letter, 0)
                poly[str(exp)] = poly.get(str(exp), 0) + coeff_val
            elif standalone_num:
                poly['0'] = poly.get('0', 0) + int(standalone_num)

        return cls(poly=poly, base=base, coeff=1)

    @staticmethod
    def int_to_key(exp_str: str) -> str:
        if not rust_core: raise RuntimeError("Rust core is not enabled, cannot format key.")
        return rust_core.AoPValue.int_to_key(exp_str)

    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for +: '{type(other).__name__}'")
        return AoPValue(_rust_obj=self._rust_obj.__add__(other._rust_obj))

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for -: '{type(other).__name__}'")
        return AoPValue(_rust_obj=self._rust_obj.__sub__(other._rust_obj))

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for *: '{type(other).__name__}'")
        return AoPValue(_rust_obj=self._rust_obj.__mul__(other._rust_obj))

    def __pow__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for **: '{type(other).__name__}'")
        return AoPValue(_rust_obj=self._rust_obj.power(other._rust_obj))

    def to_numerical(self) -> int:
        return self._rust_obj.to_numerical()

    def __str__(self) -> str:
        return str(self._rust_obj)

    def __repr__(self) -> str:
        return self._rust_obj.__repr__()

    # The __getstate__ method tells pickle what data to save.
    def __getstate__(self):
        """Return state for pickling."""
        # We return a tuple of the data needed to reconstruct the object.
        # The Rust object itself is the source of truth.
        return (
            self._rust_obj.coeff,  # This is the SymbolicCoefficient object
            self._rust_obj.get_poly(),
            self._rust_obj.base
        )

    # The __setstate__ method tells pickle how to create the object from saved data.
    def __setstate__(self, state):
        """Restore state from pickling."""
        # Unpack the state tuple
        coeff, poly, base = state

        # We need a new constructor in Rust that can take the SymbolicCoefficient directly.
        # For now, we'll assume we add one.
        self._rust_obj = rust_core.AoPValue.from_state(coeff, poly, base)
