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

    def __init__(self, poly: Optional[Dict[str, int]] = None, base: int = 10, coeff: Optional[int] = None):
        if not rust_core:
            raise RuntimeError("Rust core is not enabled.")
        final_coeff = coeff if coeff is not None else 1
        # The Rust constructor was updated to take coeff.
        self._rust_obj = rust_core.AoPValue(poly, base, final_coeff)

    @classmethod
    def from_number(cls, n: int, base: int = 10) -> 'AoPValue':
        if not rust_core: raise RuntimeError("Rust core is not enabled.")
        instance = cls.__new__(cls)
        instance._rust_obj = rust_core.AoPValue.from_number(n, base)
        return instance

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

    # --- Start of explicit wrapper methods for Pylance ---
    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for +: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = self._rust_obj.__add__(other._rust_obj)
        return new_instance

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for -: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = self._rust_obj.__sub__(other._rust_obj)
        return new_instance

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for *: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = self._rust_obj.__mul__(other._rust_obj)
        return new_instance

    def __pow__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for **: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = self._rust_obj.power(other._rust_obj)
        return new_instance

    def get_coeff_as_power(self) -> Optional[tuple[int, int]]:
        """Returns the coefficient as a power tuple (base, exponent) if it is a power, else None."""
        return self._rust_obj.get_coeff_as_power()

    def to_numerical(self) -> int:
        return self._rust_obj.to_numerical()

    def __str__(self) -> str:
        return self._rust_obj.__str__()

    def __repr__(self) -> str:
        return self._rust_obj.__repr__()

    def __reduce__(self):
        """Tells Python's pickle module how to serialize this object."""
        rust_poly_str_keys = self._rust_obj.get_poly()
        rust_base = self._rust_obj.base
        rust_coeff = self._rust_obj.coeff
        return (self.__class__, (rust_poly_str_keys, rust_base, rust_coeff))
