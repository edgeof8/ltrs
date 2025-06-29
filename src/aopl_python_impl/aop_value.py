# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional
import math
import logging
from .aop_logger import log_pow

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

    # --- NEW STATIC METHOD ---
    @staticmethod
    def from_number(n: int, base: int = 10) -> 'AoPValue':
        """Creates an AoPValue instance from a standard numerical integer."""
        if n == 0:
            return AoPValue({}, base=base)

        is_negative = n < 0
        if is_negative:
            n = -n

        poly = {}
        exp = 0
        while n > 0:
            n, remainder = divmod(n, base)
            if remainder != 0:
                poly[exp] = remainder
            exp += 1

        return AoPValue(poly, base=base, is_negative=is_negative)

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
        # --- Tier 1: The "Hyper-Fast Path" (Exploiting the Logarithmic Shortcut) ---
        # This path handles (base^(10^k)) ^ (base^n) using pure integer math.
        # It's the fastest possible path for these specific hyper-power calculations.
        is_self_pure_power = len(self.poly) == 1 and list(self.poly.values())[0] == 1
        is_other_pure_power = len(other.poly) == 1 and list(other.poly.values())[0] == 1

        if is_self_pure_power and is_other_pure_power and self.base == 10:
            self_exp = list(self.poly.keys())[0]
            # Check if the base's exponent is itself a clean power of 10
            if self_exp > 0 and self_exp % 10 == 0:
                try:
                    k = int(math.log10(self_exp))
                    if 10**k == self_exp: # It's a perfect power of 10
                        n = list(other.poly.keys())[0]
                        log_pow(f"HYPER-FAST PATH: Detected (10^(10^{k}))^(10^{n}). New exponent is 10^({k}+{n}).")
                        new_final_exponent = 10**(k + n)
                        return AoPValue({new_final_exponent: 1}, base=self.base)
                except (ValueError, TypeError):
                    # Not a perfect power of 10, fall through to the next path
                    pass

        # --- Tier 2: The "General Fast Path" (Symbolic Exponentiation) ---
        # This handles (base^k) ^ other where k is not a power of 10.
        # It's slower than Tier 1 but avoids converting `other` to a massive integer.
        if is_self_pure_power:
            # We are in the simple case: (base^k) ^ other
            k = list(self.poly.keys())[0]
            k_as_aop = AoPValue.from_number(k, base=self.base)
            new_exponent_as_aop = k_as_aop * other
            new_exponent_numerical = new_exponent_as_aop.to_numerical()
            return AoPValue({new_exponent_numerical: 1}, base=self.base, is_negative=self.is_negative and (new_exponent_numerical % 2 == 1))

        # --- Tier 3: The General-Purpose Algorithm (Exponentiation by Squaring) ---
        # This is the fallback for all other cases (e.g., (a+b)^c).
        # It converts the exponent to a numerical value.
        log_pow(f"GENERAL PATH: Calculating ({self!r}) ^ ({other!r})")
        n_int = other.to_numerical()
        if n_int < 0: raise ValueError("Exponent must be a non-negative integer.")

        if n_int == 0: return AoPValue({0: 1}, self.base)
        if n_int == 1: return self

        # Standard square-and-multiply algorithm
        result = AoPValue({0: 1}, self.base)
        current_base = self
        while n_int > 0:
            if n_int % 2 == 1: result *= current_base
            current_base *= current_base
            n_int //= 2
        return result

    def __repr__(self) -> str:
        # --- MODIFIED: Remove redundant base display ---
        poly_str = ", ".join(f"@{e}:{c}" for e, c in sorted(self.poly.items(), reverse=True))
        if not poly_str:
            poly_str = "0"
        sign = "-" if self.is_negative else ""
        return f"AoP({sign}{{{poly_str}}})"
