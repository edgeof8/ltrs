# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional
import math

class AoPValue:
    def __init__(self, poly: Optional[Dict[int, int]] = None, base: int = 10):
        self.poly: Dict[int, int] = poly if poly is not None else {}
        self.base = base
        self.poly = {e:c for e, c in self.poly.items() if c != 0}

    def _simplify(self):
        """
        Normalizes the polynomial by handling all carries. This is a single-pass
        implementation that is more robust and correct than the previous version.
        It processes exponents from lowest to highest.
        """
        if not self.poly:
            return

        new_poly = {}
        carry = 0
        # Process all existing exponents in increasing order
        max_exp = max(self.poly.keys())
        for exp in range(max_exp + 2): # Go one beyond to handle final carry
            coeff = self.poly.get(exp, 0) + carry
            if coeff == 0:
                continue

            carry, remainder = divmod(coeff, self.base)
            if remainder != 0:
                new_poly[exp] = remainder

        self.poly = new_poly

    def to_numerical(self) -> int:
        total = 0
        for exp, coeff in self.poly.items():
            total += coeff * (self.base ** exp)
        return total

    def to_decimal_string(self) -> str:
        """Translates the sparse polynomial into a full decimal string."""
        if not self.poly:
            return "0"

        # Find the highest power to determine the length of the number
        max_exponent = max(self.poly.keys())

        # Create a list of digits, initialized to 0
        # The length is max_exponent + 1 (e.g., 10^2 needs 3 digits: 1, 0, 0)
        num_digits = max_exponent + 1
        digits = [0] * num_digits

        # Place the coefficients at the correct positions
        for exp, coeff in self.poly.items():
            # This assumes coefficients are single digits after simplification
            # A more robust version would handle multi-digit coefficients by carrying over
            digits[exp] = coeff

        # The list is in reverse order (index 0 is the 1s place), so reverse it and join
        return "".join(map(str, reversed(digits)))


    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        new_poly = self.poly.copy()
        for exp, coeff in other.poly.items():
            new_poly[exp] = new_poly.get(exp, 0) + coeff
        new_val = AoPValue(new_poly, self.base)
        new_val._simplify()
        return new_val

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        new_poly = self.poly.copy()
        for exp, coeff in other.poly.items():
            new_poly[exp] = new_poly.get(exp, 0) - coeff
        new_val = AoPValue(new_poly, self.base)
        return new_val

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        new_poly: Dict[int, int] = {}
        if not self.poly or not other.poly: return AoPValue(base=self.base)
        for exp1, coeff1 in self.poly.items():
            for exp2, coeff2 in other.poly.items():
                new_poly[exp1 + exp2] = new_poly.get(exp1 + exp2, 0) + (coeff1 * coeff2)
        new_val = AoPValue(new_poly, self.base)
        new_val._simplify()
        return new_val

    def __pow__(self, other: 'AoPValue') -> 'AoPValue':
        try:
            n = other.to_numerical()
            if n < 0 or n != int(n): raise ValueError
        except Exception:
            raise ValueError("Exponent must be a non-negative integer.")

        n_int = int(n)
        if n_int == 0: return AoPValue({0: 1}, self.base)
        if n_int == 1: return self

        result = self
        for _ in range(n_int - 1):
            result = result * self
        return result

    def __repr__(self) -> str:
        # A more debug-friendly representation
        poly_str = ", ".join(f"{c}*B^{e}" for e, c in sorted(self.poly.items(), reverse=True))
        if not poly_str:
            poly_str = "0"
        return f"AoPValue(poly={{{poly_str}}}, base={self.base})"
