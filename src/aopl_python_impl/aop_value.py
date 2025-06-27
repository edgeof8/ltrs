# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional
import math

class AoPValue:
    def __init__(self, poly: Optional[Dict[int, int]] = None, base: int = 10, is_negative: bool = False):
        self.poly: Dict[int, int] = poly if poly is not None else {}
        self.base = base
        self.is_negative = is_negative
        self.poly = {e:c for e, c in self.poly.items() if c != 0}

    def _simplify(self):
        """
        Normalizes the polynomial by handling carries for positive coefficients.
        It processes exponents from lowest to highest, ensuring coefficients are within base range.
        This method does not handle sign determination, which is managed by higher-level operations.
        """
        if not self.poly:
            return

        new_poly = {}
        carry = 0
        max_exp = max(self.poly.keys(), default=0)
        for exp in range(max_exp + 2):  # Go one beyond to handle final carry
            coeff = self.poly.get(exp, 0) + carry
            if coeff == 0:
                continue

            carry, remainder = divmod(coeff, self.base)
            if remainder < 0:
                carry -= 1
                remainder += self.base
            if remainder != 0:
                new_poly[exp] = remainder

        if carry > 0:
            new_poly[max_exp + 1] = carry

        self.poly = new_poly

    def to_numerical(self) -> int:
        total = 0
        for exp, coeff in self.poly.items():
            total += coeff * (self.base ** exp)
        return -total if self.is_negative else total

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
            digits[exp] = coeff

        # The list is in reverse order (index 0 is the 1s place), so reverse it and join
        result = "".join(map(str, reversed(digits)))
        return "-" + result if self.is_negative else result


    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        if self.is_negative == other.is_negative:
            from multiprocessing import Pool
            import os

            def process_batch(exps, poly1, poly2, base):
                result = {}
                for exp in exps:
                    coeff = poly1.get(exp, 0) + poly2.get(exp, 0)
                    if coeff != 0:
                        result[exp] = coeff
                return result

            # Split exponents into multiple batches for parallel processing to maximize CPU usage
            all_exps = sorted(set(self.poly.keys()) | set(other.poly.keys()))
            if len(all_exps) > 10:  # Use parallel processing only for large polynomials
                # Determine number of processes based on CPU count or a reasonable maximum
                num_processes = min(8, max(2, os.cpu_count() or 2))
                batch_size = max(1, len(all_exps) // num_processes)
                batches = [all_exps[i:i + batch_size] for i in range(0, len(all_exps), batch_size)]

                with Pool(num_processes) as pool:
                    results = pool.starmap(process_batch, [
                        (batch, self.poly, other.poly, self.base) for batch in batches
                    ])

                # Combine results from all batches
                new_poly = {}
                for result in results:
                    new_poly.update(result)
            else:
                new_poly = {}
                for exp in all_exps:
                    coeff = self.poly.get(exp, 0) + other.poly.get(exp, 0)
                    if coeff != 0:
                        new_poly[exp] = coeff

            result = AoPValue(new_poly, self.base, self.is_negative)
            result._simplify()
            return result
        else:
            # Subtract the magnitudes based on sign
            if self.is_negative:
                return other - AoPValue(self.poly, self.base)
            else:
                return self - AoPValue(other.poly, other.base)

    def _compare_magnitude(self, other: 'AoPValue') -> int:
        """
        Compares the magnitude of two polynomials.
        Returns 1 if self > other, -1 if self < other, 0 if equal.
        """
        self_exps = sorted(self.poly.keys(), reverse=True)
        other_exps = sorted(other.poly.keys(), reverse=True)

        if not self_exps and not other_exps:
            return 0
        if not self_exps:
            return -1
        if not other_exps:
            return 1

        max_self_exp = self_exps[0]
        max_other_exp = other_exps[0]

        if max_self_exp != max_other_exp:
            return 1 if max_self_exp > max_other_exp else -1

        for exp in self_exps:
            self_coeff = self.poly.get(exp, 0)
            other_coeff = other.poly.get(exp, 0)
            if self_coeff != other_coeff:
                return 1 if self_coeff > other_coeff else -1
        return 0

    def __sub__(self, other: 'AoPValue') -> 'AoPValue':
        if self.is_negative == other.is_negative:
            # Same sign: compare magnitudes and subtract accordingly
            mag_compare = self._compare_magnitude(other)
            if mag_compare == 0:
                return AoPValue({}, self.base)
            elif (mag_compare > 0 and not self.is_negative) or (mag_compare < 0 and self.is_negative):
                # self is larger in magnitude (or negative and smaller)
                new_poly = self.poly.copy()
                for exp, coeff in other.poly.items():
                    new_poly[exp] = new_poly.get(exp, 0) - coeff
                result = AoPValue(new_poly, self.base, self.is_negative)
            else:
                # other is larger in magnitude
                new_poly = other.poly.copy()
                for exp, coeff in self.poly.items():
                    new_poly[exp] = new_poly.get(exp, 0) - coeff
                result = AoPValue(new_poly, self.base, not self.is_negative)
            # Handle borrowing for negative coefficients before simplification
            result._borrow_for_negative_coeffs()
            result._simplify()
            return result
        else:
            # Different signs: add magnitudes with appropriate sign
            new_poly = self.poly.copy()
            for exp, coeff in other.poly.items():
                new_poly[exp] = new_poly.get(exp, 0) + coeff
            result = AoPValue(new_poly, self.base, self.is_negative)
            result._simplify()
            return result

    def _borrow_for_negative_coeffs(self):
        """
        Handles borrowing for negative coefficients to ensure all coefficients are non-negative.
        This method adjusts the polynomial to eliminate negative coefficients by borrowing
        from higher exponents, handling dictionary updates safely to avoid key errors.
        """
        if not self.poly:
            return

        new_poly = self.poly.copy()
        exps = sorted(new_poly.keys())
        i = 0
        while i < len(exps):
            exp = exps[i]
            coeff = new_poly.get(exp, 0)  # Safe access in case exp was deleted
            if coeff < 0:
                # Borrow from the next higher exponent
                borrow_exp = exp + 1
                while coeff < 0:
                    if borrow_exp not in new_poly:
                        new_poly[borrow_exp] = 0
                    new_poly[borrow_exp] -= 1
                    coeff += self.base
                    if new_poly[borrow_exp] == 0:
                        del new_poly[borrow_exp]
                    else:
                        # Ensure borrow_exp is in exps if it still exists
                        if borrow_exp not in exps:
                            exps.append(borrow_exp)
                            exps.sort()
                    borrow_exp += 1
                if coeff != 0:
                    new_poly[exp] = coeff
                else:
                    if exp in new_poly:
                        del new_poly[exp]
                    # Remove exp from exps if it was deleted
                    if exp in exps:
                        exps.remove(exp)
            else:
                i += 1
        self.poly = {exp: coeff for exp, coeff in new_poly.items() if coeff != 0}

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        if not self.poly or not other.poly: return AoPValue(base=self.base)
        new_poly: Dict[int, int] = {}
        # Optimize by iterating over the smaller polynomial to reduce iterations
        if len(self.poly) <= len(other.poly):
            smaller, larger = self.poly, other.poly
        else:
            smaller, larger = other.poly, self.poly

        for exp1, coeff1 in smaller.items():
            for exp2, coeff2 in larger.items():
                exp_sum = exp1 + exp2
                if exp_sum in new_poly:
                    new_poly[exp_sum] += coeff1 * coeff2
                else:
                    new_poly[exp_sum] = coeff1 * coeff2

        is_negative = self.is_negative != other.is_negative
        new_val = AoPValue(new_poly, self.base, is_negative)
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

        # Use square-and-multiply algorithm for efficient exponentiation
        result = AoPValue({0: 1}, self.base)
        base = AoPValue(self.poly.copy(), self.base, self.is_negative)
        is_negative = self.is_negative and (n_int % 2 == 1)
        while n_int > 0:
            if n_int % 2 == 1:
                # Minimize object creation by updating result in-place if possible
                result = result * base
            # Square the base in-place to reduce copying
            base = base * base
            n_int //= 2
        result.is_negative = is_negative
        return result

    def __repr__(self) -> str:
        # A more debug-friendly representation
        poly_str = ", ".join(f"{c}*B^{e}" for e, c in sorted(self.poly.items(), reverse=True))
        if not poly_str:
            poly_str = "0"
        sign = "-" if self.is_negative else ""
        return f"AoPValue(poly={sign}{{{poly_str}}}, base={self.base})"
