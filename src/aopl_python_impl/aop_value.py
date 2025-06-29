# aopl_python_impl/aop_value.py
from __future__ import annotations
from typing import Dict, Optional
from itertools import zip_longest
import math
import logging
from .aop_logger import log_pow
from .definitions import LETTER_TO_EXPONENT_MAP, EXPONENT_TO_LETTER_MAP
from .aop_types import SymbolicPowerResult

# --- NEW: Top-level function for multiprocessing ---
# This function must be at the top level of the module so that it can be
# pickled and sent to worker processes.
def _add_poly_batch(exps, poly1, poly2):
    """Processes a batch of exponents for polynomial addition."""
    result = {}
    for exp in exps:
        coeff = poly1.get(exp, 0) + poly2.get(exp, 0)
        if coeff != 0:
            result[exp] = coeff
    return result

def key_to_int(key_str: str, _base: int = 10) -> int:
    """
    Converts a canonical AoP string exponent (e.g., "b", "Z", "2c5a", "0")
    to its numerical integer value.
    """
    if key_str == "0": # Canonical string for exponent 0
        return 0

    total_exp_val = 0
    current_coeff_str = ""
    current_letter_str = ""

    # Iterate through the string to parse it
    for char in key_str:
        if char.isdigit():
            current_coeff_str += char
        elif char.isalpha():
            # Process the previous coeff/letter group (if any)
            if not current_coeff_str.isnumeric() and not current_letter_str.isalpha():
                # This handles cases like "b" or "Z" where there's no explicit coeff
                coeff = 1
            elif current_coeff_str.isnumeric():
                coeff = int(current_coeff_str)
            else:
                raise ValueError(f"Invalid AoP key format: '{key_str}'. Expected digit or letter, got '{char}' after non-coeff.")

            current_letter_exp = LETTER_TO_EXPONENT_MAP.get(char, 0)
            total_exp_val += coeff * current_letter_exp

            current_coeff_str = "" # Reset for next group
            current_letter_str = "" # Reset
        else:
            raise ValueError(f"Invalid character in AoP key string: '{key_str}' (char: '{char}')")

    # Handle cases like "5" (a standalone number exponent)
    if current_coeff_str.isnumeric() and not current_letter_str.isalpha():
        total_exp_val += int(current_coeff_str) # Assume it's 5 * 10^0

    return total_exp_val

def int_to_key(exp_num: int, _base: int = 10) -> str:
    """
    Converts a numerical integer exponent to its canonical AoP string representation.
    e.g., 1 -> "a", 2 -> "b", 26 -> "A", 100 -> "Z", 101 -> "Za" (or aZ based on canonical form)
    """
    if exp_num == 0:
        return "0" # Canonical string for exponent 0

    parts = []
    remaining_exp = exp_num

    # Use EXPONENT_TO_LETTER_MAP for direct lookups
    # Sort by numerical value, largest first, to build canonical form
    # EXPONENT_TO_LETTER_MAP is typically {1:'a', 2:'b', ..., 100:'Z'}

    # It's crucial that EXPONENT_TO_LETTER_MAP is robust.
    # We need to use the one from definitions.py that correctly maps values like 100 to 'Z'.
    # Let's assume it's available and correct.

    # Iterate through possible exponent values from highest to lowest
    # This list needs to be derived from LETTER_TO_EXPONENT_MAP's values
    sorted_exp_values = sorted(LETTER_TO_EXPONENT_MAP.values(), reverse=True)
    sorted_exp_values = list(dict.fromkeys(sorted_exp_values)) # Remove duplicates if 'z' and 'Z' both map to 100

    for val in sorted_exp_values:
        if val == 0: continue # Skip 0, handled by "0" return

        count = remaining_exp // val
        if count > 0:
            letter = EXPONENT_TO_LETTER_MAP.get(val, str(val)) # Fallback to number if no letter
            parts.append(f"{count}{letter}" if count > 1 else letter)
            remaining_exp -= count * val

    if remaining_exp > 0:
        # Append any remaining numerical value that couldn't be mapped to letters
        # This handles cases like 101 -> "Z1" if 1 is not a letter or if it's already used
        parts.append(str(remaining_exp))

    return "".join(parts)

class AoPValue:
    def __init__(self, poly: Optional[Dict[str, int]] = None, base: int = 10, is_negative: bool = False):
        self.poly: Dict[str, int] = poly if poly is not None else {}
        self.base = base
        self.is_negative = is_negative
        self.poly = {e: c for e, c in self.poly.items() if c != 0}

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
        # Convert string keys to numerical for ordering
        exp_map = {key_to_int(exp, self.base): exp for exp in self.poly.keys()}
        max_exp_num = max(exp_map.keys(), default=0) if exp_map else 0
        for exp_num in range(max_exp_num + 2):  # Go one beyond to handle final carry
            exp_str = exp_map.get(exp_num, int_to_key(exp_num, self.base))
            coeff = self.poly.get(exp_str, 0) + carry
            if coeff == 0:
                continue

            carry, remainder = divmod(coeff, self.base)
            if remainder < 0:
                carry -= 1
                remainder += self.base
            if remainder != 0:
                new_poly[exp_str] = remainder

        if carry > 0:
            carry_exp_str = int_to_key(max_exp_num + 1, self.base)
            new_poly[carry_exp_str] = carry

        self.poly = new_poly

    def to_numerical(self) -> int:
        total = 0
        for exp_str, coeff in self.poly.items():
            exp_num = key_to_int(exp_str, self.base)
            total += coeff * (self.base ** exp_num)
        return -total if self.is_negative else total

    def to_decimal_string(self) -> str:
        """Translates the sparse polynomial into a full decimal string."""
        if not self.poly:
            return "0"

        # Find the highest power to determine the length of the number
        max_exponent = max(key_to_int(exp, self.base) for exp in self.poly.keys()) if self.poly else 0

        # Create a list of digits, initialized to 0
        # The length is max_exponent + 1 (e.g., 10^2 needs 3 digits: 1, 0, 0)
        num_digits = max_exponent + 1
        digits = [0] * num_digits

        # Place the coefficients at the correct positions
        for exp_str, coeff in self.poly.items():
            exp_num = key_to_int(exp_str, self.base)
            digits[exp_num] = coeff

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
        exp_num = 0
        while n > 0:
            n, remainder = divmod(n, base)
            if remainder != 0:
                exp_str = int_to_key(exp_num, base)
                poly[exp_str] = remainder
            exp_num += 1

        return AoPValue(poly, base=base, is_negative=is_negative)

    def __add__(self, other: 'AoPValue') -> 'AoPValue':
        if self.is_negative == other.is_negative:
            from multiprocessing import Pool
            import os

            # Split exponents into multiple batches for parallel processing to maximize CPU usage
            all_exps = sorted(set(self.poly.keys()) | set(other.poly.keys()), key=lambda x: key_to_int(x, self.base))
            if len(all_exps) > 10:  # Use parallel processing only for large polynomials
                # Determine number of processes based on CPU count or a reasonable maximum
                num_processes = min(8, max(2, os.cpu_count() or 2))
                batch_size = max(1, len(all_exps) // num_processes)
                batches = [all_exps[i:i + batch_size] for i in range(0, len(all_exps), batch_size)]

                with Pool(processes=num_processes) as pool:
                    results = pool.starmap(_add_poly_batch, [
                        (batch, self.poly, other.poly) for batch in batches
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
        self_exps = sorted(self.poly.keys(), key=lambda x: key_to_int(x, self.base), reverse=True)
        other_exps = sorted(other.poly.keys(), key=lambda x: key_to_int(x, self.base), reverse=True)

        if not self_exps and not other_exps:
            return 0
        if not self_exps:
            return -1
        if not other_exps:
            return 1

        max_self_exp_num = key_to_int(self_exps[0], self.base)
        max_other_exp_num = key_to_int(other_exps[0], self.base)

        if max_self_exp_num != max_other_exp_num:
            return 1 if max_self_exp_num > max_other_exp_num else -1

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
        exps = sorted(new_poly.keys(), key=lambda x: key_to_int(x, self.base))
        i = 0
        while i < len(exps):
            exp = exps[i]
            coeff = new_poly.get(exp, 0)  # Safe access in case exp was deleted
            if coeff < 0:
                # Borrow from the next higher exponent
                borrow_exp_num = key_to_int(exp, self.base) + 1
                borrow_exp = int_to_key(borrow_exp_num, self.base)
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
                            exps.sort(key=lambda x: key_to_int(x, self.base))
                    borrow_exp_num += 1
                    borrow_exp = int_to_key(borrow_exp_num, self.base)
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

    # --- SPECIALIZED MULTIPLIERS (New private methods) ---

    def _get_trailing_zeros(self) -> int:
        """Helper to find the number of trailing zeros (lowest exponent)."""
        if not self.poly:
            return 0
        return min(key_to_int(exp, self.base) for exp in self.poly.keys()) if self.poly else 0

    def _strip_trailing_zeros(self, zero_count: int) -> 'AoPValue':
        """Helper to return a new AoPValue with zeros removed."""
        if zero_count == 0:
            return self
        new_poly = {int_to_key(key_to_int(exp, self.base) - zero_count, self.base): coeff for exp, coeff in self.poly.items()}
        return AoPValue(new_poly, self.base, self.is_negative)

    def _dense_mul(self, other: 'AoPValue') -> 'AoPValue':
        """
        The original, robust multiplication algorithm for dense polynomials.
        """
        if not self.poly or not other.poly: return AoPValue(base=self.base)
        new_poly: Dict[str, int] = {}
        # Optimize by iterating over the smaller polynomial to reduce iterations
        if len(self.poly) <= len(other.poly):
            smaller, larger = self.poly, other.poly
        else:
            smaller, larger = other.poly, self.poly

        for exp1, coeff1 in smaller.items():
            for exp2, coeff2 in larger.items():
                exp1_num = key_to_int(exp1, self.base)
                exp2_num = key_to_int(exp2, self.base)
                exp_sum_num = exp1_num + exp2_num
                exp_sum = int_to_key(exp_sum_num, self.base)
                if exp_sum in new_poly:
                    new_poly[exp_sum] += coeff1 * coeff2
                else:
                    new_poly[exp_sum] = coeff1 * coeff2

        is_negative = self.is_negative != other.is_negative
        new_val = AoPValue(new_poly, self.base, is_negative)
        new_val._simplify()
        return new_val

    def __imul__(self, other: 'AoPValue') -> 'AoPValue':
        """In-place multiplication."""
        result = self * other
        self.poly = result.poly
        self.is_negative = result.is_negative
        return self

    def _split_at_midpoint(self) -> tuple['AoPValue', 'AoPValue']:
        """
        Splits a polynomial into two halves for Karatsuba's algorithm.
        Returns (low_part, high_part)
        """
        if not self.poly:
            return AoPValue(base=self.base), AoPValue(base=self.base)

        # Find the midpoint based on the degree of the polynomial
        max_degree = max(key_to_int(exp, self.base) for exp in self.poly.keys()) if self.poly else 0
        mid = (max_degree // 2) + 1

        low_poly = {}
        high_poly = {}

        for exp, coeff in self.poly.items():
            exp_num = key_to_int(exp, self.base)
            if exp_num < mid:
                low_poly[exp] = coeff
            else:
                high_exp = int_to_key(exp_num - mid, self.base)
                high_poly[high_exp] = coeff  # Shift high-degree terms down

        return AoPValue(low_poly, self.base), AoPValue(high_poly, self.base)

    def _karatsuba_mul(self, other: 'AoPValue') -> 'AoPValue':
        """
        Multiplies two polynomials using the Karatsuba algorithm, which is
        more efficient for large, dense polynomials (O(n^1.585) vs O(n^2)).
        """
        if not self.poly or not other.poly:
            return AoPValue(base=self.base)

        # Base case for recursion
        if len(self.poly) < 2 or len(other.poly) < 2:
            return self._dense_mul(other)

        # 1. Split polynomials into low and high parts
        a, b = self._split_at_midpoint()   # self = a + b*x^m
        c, d = other._split_at_midpoint()  # other = c + d*x^m

        # Determine the midpoint m for recombination
        m = (max(max(key_to_int(exp, self.base) for exp in self.poly.keys()) if self.poly else 0,
                 max(key_to_int(exp, self.base) for exp in other.poly.keys()) if other.poly else 0) // 2) + 1

        # 2. Recursive calls
        ac = a * c       # z0 = ac
        bd = b * d       # z2 = bd
        ad_plus_bc = (a + b) * (c + d) - ac - bd  # z1 = (a+b)(c+d) - ac - bd

        # 3. Recombine the results
        # Result = z2 * x^(2m) + z1 * x^m + z0

        # Shift bd by 2m
        term_bd_shifted = AoPValue({int_to_key(key_to_int(exp, self.base) + 2 * m, self.base): coeff for exp, coeff in bd.poly.items()}, base=self.base)

        # Shift ad_plus_bc by m
        term_adbc_shifted = AoPValue({int_to_key(key_to_int(exp, self.base) + m, self.base): coeff for exp, coeff in ad_plus_bc.poly.items()}, base=self.base)

        # Combine all parts. We can do this with our existing addition.
        result = ac + term_adbc_shifted + term_bd_shifted
        result.is_negative = self.is_negative != other.is_negative
        result._simplify()

        return result

    # --- THE NEW DISPATCHER ---

    def __mul__(self, other: 'AoPValue') -> 'AoPValue':
        """
        Intelligent Dispatcher for multiplication. It analyzes the operands
        and chooses the most efficient algorithm based on benchmark data.
        """
        # Define a much higher threshold based on benchmark data.
        # Karatsuba only wins at 2048 bits and above for dense numbers.
        KARATSUBA_THRESHOLD_BITS = 2048

        # --- Tier 0: The Trailing Zero Shortcut ---
        self_zeros = self._get_trailing_zeros()
        other_zeros = self._get_trailing_zeros()

        # Use this shortcut if there's a significant number of zeros to strip
        if self_zeros > 5 and other_zeros > 5:
            log_pow(f"DISPATCHER: Using Trailing Zero Shortcut.")
            # 1. Strip the zeros to get the "heads"
            self_head = self._strip_trailing_zeros(self_zeros)
            other_head = other._strip_trailing_zeros(other_zeros)

            # 2. Multiply the heads using the general dispatcher (recursive call)
            result_head = self_head * other_head  # This recursive call is key

            # 3. Stitch the result back together by adding the exponents
            total_zeros = self_zeros + other_zeros
            final_poly = {int_to_key(key_to_int(exp, self.base) + total_zeros, self.base): coeff for exp, coeff in result_head.poly.items()}
            return AoPValue(final_poly, self.base, result_head.is_negative)

        # Get the bit length of the larger number
        max_bits = max(self.to_numerical().bit_length(), other.to_numerical().bit_length())

        # --- NEW, SIMPLIFIED DISPATCH LOGIC ---
        # 1. If numbers are very large and dense, use Karatsuba.
        if max_bits >= KARATSUBA_THRESHOLD_BITS:
            log_pow(f"DISPATCHER: Using Karatsuba Multiplication for very large numbers ({max_bits} bits).")
            return self._karatsuba_mul(other)
        # 2. For everything else, use the superior AoP optimized algorithm.
        else:
            log_pow(f"DISPATCHER: Using AoP Optimized Multiplication for numbers ({max_bits} bits).")
            return self._dense_mul(other)

    def __pow__(self, other: 'AoPValue') -> 'AoPValue | SymbolicPowerResult':
        # --- POWER DISPATCHER ---
        # We will always attempt the symbolic path first.
        # This creates a representation of the operation without computing it.
        # The 'to_numerical' or 'format' methods will handle the actual computation.

        log_pow(f"Creating SymbolicPowerResult for ({self!r}) ^ ({other!r})")
        return SymbolicPowerResult(self, other)

    def is_pure_power(self) -> bool:
        """Check if the value is a pure power (single term with coefficient 1)."""
        return len(self.poly) == 1 and list(self.poly.values())[0] == 1

    def get_single_exponent_value(self) -> int:
        """Gets the integer exponent value, assuming it's a pure power. For internal use."""
        if self.is_pure_power():
            return key_to_int(list(self.poly.keys())[0], self.base)
        raise ValueError("Cannot get single exponent from a complex polynomial.")

    def is_small_integer(self) -> bool:
        """Check if the value is a small integer (can be converted to numerical easily)."""
        if len(self.poly) == 0:
            return True
        max_exp_num = max(key_to_int(exp, self.base) for exp in self.poly.keys()) if self.poly else 0
        if max_exp_num > 5:  # Arbitrary threshold for small exponent
            return False
        try:
            num_val = self.to_numerical()
            return abs(num_val) < 1000  # Another threshold for small integer
        except OverflowError:
            return False

    def __repr__(self) -> str:
        # --- MODIFIED: Remove redundant base display ---
        poly_str = ", ".join(f"@{e}:{c}" for e, c in sorted(self.poly.items(), key=lambda x: key_to_int(x[0], self.base), reverse=True))
        if not poly_str:
            poly_str = "0"
        sign = "-" if self.is_negative else ""
        return f"AoP({sign}{{{poly_str}}})"
