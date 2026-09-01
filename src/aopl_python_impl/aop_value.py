# aopl_python_impl/aop_value.py
#
# This module defines the `AoPValue` class, which is the Python interface
# to the high-performance `AoPValue` struct defined in the Rust core.
# This class acts as a handle, creating Rust objects and dispatching
# all mathematical operations (+, *, **, etc.) to the compiled Rust code.
from __future__ import annotations
from typing import Dict, Optional, Any, TYPE_CHECKING
import logging
from .constants import LETTER_TO_EXPONENT_MAP # Import from constants
from .definitions import AoPError
import math
from .aop_parser import strip_digit_group_commas
import re # Keep this line

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


def _call_rust(operation):
    try:
        return operation()
    except ValueError as e:
        raise AoPError(str(e)) from e


def _terms(val: "AoPValue") -> Dict[int, int]:
    outer = int(val._rust_obj.coeff)
    if outer == 0:
        return {}
    poly = val._rust_obj.get_poly()
    if not poly:
        return {0: outer}
    return {int(exp): outer * int(coeff) for exp, coeff in poly.items() if int(coeff)}


def _is_zero(val: "AoPValue") -> bool:
    return not _terms(val)


def _try_int(val: "AoPValue") -> Optional[int]:
    try:
        return val.to_numerical()
    except AoPError:
        return None


def _from_terms(terms: Dict[int, int], base: int) -> "AoPValue":
    cleaned = {exp: coeff for exp, coeff in terms.items() if coeff}
    if not cleaned:
        return AoPValue.from_number(0, base)
    return AoPValue(poly={str(exp): coeff for exp, coeff in cleaned.items()}, base=base, coeff=1)


def _residue(val: "AoPValue", modulus: int) -> int:
    modulus = abs(int(modulus))
    if modulus == 0:
        n = _try_int(val)
        if n is None:
            raise AoPError("gcd: modulus is 0 and the other value cannot be expanded.")
        return n
    acc = 0
    base = int(val._rust_obj.base)
    for exp, coeff in _terms(val).items():
        acc = (acc + int(coeff) * pow(base, exp, modulus)) % modulus
    return acc


def _abs_value(val: "AoPValue") -> "AoPValue":
    n = _try_int(val)
    if n is not None:
        return AoPValue.from_number(abs(n), val._rust_obj.base)
    if int(val._rust_obj.coeff) < 0:
        return AoPValue.from_number(0, val._rust_obj.base) - val
    return val


def _shift_down(val: "AoPValue", k: int) -> "AoPValue":
    return _from_terms({exp - k: coeff for exp, coeff in _terms(val).items()}, val._rust_obj.base)


def _mul_base_pow(val: "AoPValue", k: int) -> "AoPValue":
    if k == 0:
        return val
    return val * AoPValue(poly={str(k): 1}, base=val._rust_obj.base, coeff=1)


def _gcd_values(left: "AoPValue", right: "AoPValue") -> "AoPValue":
    a, b = left, right
    base = int(a._rust_obj.base)
    for _ in range(10_000):
        if _is_zero(b):
            return _abs_value(a)
        if _is_zero(a):
            return _abs_value(b)
        na, nb = _try_int(a), _try_int(b)
        if na is not None and nb is not None:
            return AoPValue.from_number(math.gcd(na, nb), base)
        if nb is not None:
            a, b = b, AoPValue.from_number(_residue(a, nb), base)
            continue
        if na is not None:
            b = AoPValue.from_number(_residue(b, na), base)
            continue
        terms_a, terms_b = _terms(a), _terms(b)
        k = min(min(terms_a), min(terms_b))
        if k > 0:
            return _mul_base_pow(_gcd_values(_shift_down(a, k), _shift_down(b, k)), k)
        ea, eb = max(terms_a), max(terms_b)
        if ea < eb:
            a, b = b, a
            ea, eb = eb, ea
            terms_a, terms_b = terms_b, terms_a
        if ea == eb:
            a = a - b
            continue
        d = ea - eb
        q = max(abs(terms_a[ea]) // abs(terms_b[eb]), 1)
        mono = AoPValue(poly={str(d): 1}, base=base, coeff=q)
        a = a - mono * b
    raise AoPError("gcd did not converge.")


class AoPValue:
    _rust_obj: Any

    def __init__(self, poly: Optional[Dict[str, int]] = None, base: int = 10, coeff: Optional[int] = None):
        if not rust_core:
            raise RuntimeError("Rust core is not enabled.")
        final_coeff = coeff if coeff is not None else 1
        self._rust_obj = rust_core.AoPValue(poly, base, final_coeff)

    @classmethod
    def from_number(cls, n: int, base: int = 10) -> 'AoPValue':
        if not rust_core: raise RuntimeError("Rust core is not enabled.")
        instance = cls.__new__(cls)
        instance._rust_obj = rust_core.AoPValue.from_number(n, base)
        return instance

    @classmethod
    def from_literal(cls, literal_str: str, base: int = 10) -> 'AoPValue':
        literal_str = strip_digit_group_commas(literal_str)
        term_pattern = re.compile(r'(\d+)?([a-zA-Z])|(\d+)')
        matches = list(term_pattern.finditer(literal_str))

        # If a literal consists of just ONE term with a letter (e.g., "2b", "c", "Z"),
        # it's treated as a single scaled power, not an additive polynomial.
        if len(matches) == 1 and matches[0].group(2): # group(2) is the letter part
            match = matches[0]
            coeff_str, letter, _ = match.groups()

            main_coeff = int(coeff_str) if coeff_str else 1
            exp = LETTER_TO_EXPONENT_MAP.get(letter, 0)
            poly = {str(exp): 1} # The polynomial part is just base^exp
            # Use keyword arguments to match the __init__ signature and satisfy Pylance.
            return cls(poly=poly, base=base, coeff=main_coeff)

        # Otherwise, the literal is an additive polynomial (e.g., "b2", "2c4a").
        # The main coefficient is 1, and each term contributes to the poly map.
        poly = {}
        for match in matches:
            coeff_str, letter, standalone_num = match.groups()
            if letter:
                coeff_val = int(coeff_str) if coeff_str else 1
                exp = LETTER_TO_EXPONENT_MAP.get(letter, 0)
                poly[str(exp)] = poly.get(str(exp), 0) + coeff_val
            elif standalone_num:
                poly['0'] = poly.get('0', 0) + int(standalone_num)
        # "0" (and other all-zero literals) must not become coeff=1 with an empty poly,
        # which Rust treats as the constant 1.
        if matches and all(v == 0 for v in poly.values()):
            return cls.from_number(0, base)
        return cls(poly=poly, base=base, coeff=1)

    @staticmethod
    def int_to_key(exp_str: str) -> str:
        if not rust_core: raise RuntimeError("Rust core is not enabled, cannot format key.")
        return rust_core.AoPValue.int_to_key(exp_str)

    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for +: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = _call_rust(lambda: self._rust_obj.__add__(other._rust_obj))
        return new_instance

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for -: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = _call_rust(lambda: self._rust_obj.__sub__(other._rust_obj))
        return new_instance

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for *: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = _call_rust(lambda: self._rust_obj.__mul__(other._rust_obj))
        return new_instance

    def __truediv__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for /: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = _call_rust(lambda: self._rust_obj.__truediv__(other._rust_obj))
        return new_instance

    def __pow__(self, other: 'AoPValue') -> 'AoPValue':
        if not isinstance(other, AoPValue): raise TypeError(f"Unsupported operand type for **: '{type(other).__name__}'")
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._rust_obj = _call_rust(lambda: self._rust_obj.power(other._rust_obj))
        return new_instance

    def gcd(self, other: 'AoPValue') -> 'AoPValue':
        """Integer gcd from the sparse poly. Does not call to_numerical on huge exponents."""
        if not isinstance(other, AoPValue):
            raise TypeError(f"Unsupported operand type for gcd: '{type(other).__name__}'")
        if self._rust_obj.base != other._rust_obj.base:
            raise AoPError("Cannot operate on AoPValues with different bases.")
        return _gcd_values(self, other)

    def get_coeff_as_power(self) -> Optional[tuple[int, int]]:
        """Returns the coefficient as a power tuple (base, exponent) if it is a power, else None."""
        return self._rust_obj.get_coeff_as_power()

    def get_decomposition_str(self) -> str:
        """Generates a human-readable string of the polynomial decomposition."""
        rust_poly = self._rust_obj.get_poly()
        base = self._rust_obj.base
        coeff = self._rust_obj.coeff

        if not rust_poly:
            return str(coeff)

        # Sort terms by exponent descending for canonical output
        sorted_terms = sorted(rust_poly.items(), key=lambda item: int(item[0]), reverse=True)

        parts = [f"({v} * {base}^{k})" for k, v in sorted_terms]
        poly_str = " + ".join(parts)

        if coeff != 1:
            return f"{coeff} * ({poly_str})"
        return poly_str

    def to_numerical(self) -> int:
        return _call_rust(self._rust_obj.to_numerical)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AoPValue):
            return NotImplemented
        if self._rust_obj.base != other._rust_obj.base:
            return False
        return (
            self._rust_obj.coeff == other._rust_obj.coeff
            and self._rust_obj.get_poly() == other._rust_obj.get_poly()
        )

    def __str__(self) -> str:
        return self._rust_obj.__str__()

    def __repr__(self) -> str:
        return self._rust_obj.__repr__()

    def __reduce__(self):
        """
        Tells Python's `pickle` module how to serialize this object.
        It returns a tuple: (the callable to use for unpickling, a tuple of args for that callable).
        Here, we use the class itself as the callable and provide the constructor args.
        """
        rust_poly_str_keys = self._rust_obj.get_poly()
        rust_base = self._rust_obj.base
        rust_coeff = self._rust_obj.coeff
        return (self.__class__, (rust_poly_str_keys, rust_base, rust_coeff))
