# aopl_python_impl/aop_formatter.py
import math, cmath, decimal
from decimal import Decimal, getcontext
from typing import Callable, Union
from .definitions import OutputFormatMode, EXPONENT_TO_LETTER_MAP

getcontext().prec = 100

def _complex_to_str(c: complex, precision: int) -> str:
    if cmath.isclose(c.imag, 0):
        real_part = c.real
        if cmath.isclose(real_part, round(real_part)):
            if abs(real_part) < 1e18: return str(int(round(real_part)))
        return f"{real_part:.{precision}g}".rstrip('0').rstrip('.')
    if cmath.isclose(c.real, 0):
        if cmath.isclose(abs(c.imag), 1.0): return "j" if c.imag > 0 else "-j"
        return f"{c.imag:.{precision}g}j".rstrip('0').rstrip('.')
    r_str = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
    imag_sign = '+' if c.imag > 0 else '-'
    imag_val_str = f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.')
    imag_str = "j" if cmath.isclose(abs(c.imag), 1.0) else f"{imag_val_str}j"
    return f"({r_str}{imag_sign}{imag_str})"

# aopl_python_impl/aop_formatter.py

def _format_numeric_exponent(num: Union[Decimal, complex, float, int], base: int, get_letter: Callable, precision: int) -> str:
    if isinstance(num, complex):
        if not cmath.isclose(num.imag, 0): return _complex_to_str(num, precision)
        num_decimal = Decimal(str(num.real))
    else:
        num_decimal = Decimal(str(num))

    # FIX: Handle non-finite numbers at the very beginning to prevent crashes.
    if not num_decimal.is_finite():
        return str(num_decimal)

    if num_decimal.is_zero(): return "0"

    is_integral = (num_decimal == num_decimal.to_integral_value(rounding=decimal.ROUND_HALF_UP))
    if not is_integral:
        return f"{num_decimal:.{precision}f}".rstrip('0').rstrip('.')

    num_decimal = num_decimal.to_integral_value(rounding=decimal.ROUND_HALF_UP)

    # Try simple letter conversion first
    if num_decimal.compare(Decimal(0)) == 1 and num_decimal.compare(Decimal(51)) == -1:
        num_int = int(num_decimal)
        if letter := get_letter(num_int): return letter

    # FIX: New logic to find best "Coeff*Letter" representation
    for L_raw_exp in sorted(EXPONENT_TO_LETTER_MAP.keys(), reverse=True):
        if L_raw_exp <= 0: continue
        letter_char = get_letter(L_raw_exp)
        if not letter_char: continue
        try:
            letter_actual_value = Decimal(base) ** L_raw_exp
            if letter_actual_value.is_zero() or abs(num_decimal) < abs(letter_actual_value): continue

            # Check for divisibility
            if num_decimal % letter_actual_value == 0:
                coeff_dec = num_decimal / letter_actual_value
                if coeff_dec == coeff_dec.to_integral_value(rounding=decimal.ROUND_HALF_UP):
                    coeff_int = int(coeff_dec)
                    if coeff_int == 1: return letter_char
                    # Return as Coeff*Letter, e.g., "2c"
                    return f"{coeff_int}{letter_char}"
        except (decimal.Overflow, decimal.InvalidOperation):
            continue

    # Final fallback: plain integer string, preventing scientific notation.
    return f'{num_decimal:f}'
