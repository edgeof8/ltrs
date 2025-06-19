# aopl_python_impl/aop_formatter.py
import math, cmath, decimal
from decimal import Decimal, getcontext
from typing import Callable, Union
from .aop_value import AoPValue, AoPTerm, PracticalLimitError
from .definitions import OutputFormatMode, EXPONENT_TO_LETTER_MAP

getcontext().prec = 200

def _complex_to_str(c: complex, precision: int) -> str:
    if cmath.isclose(c.imag, 0):
        real_part = c.real
        if cmath.isclose(real_part, round(real_part)): return str(int(round(real_part)))
        return f"{real_part:.{precision}g}".rstrip('0').rstrip('.')
    if cmath.isclose(c, 0j): return "0"
    if cmath.isclose(c.real, 0):
        imag_str = "j" if cmath.isclose(abs(c.imag), 1.0) else f"{abs(c.imag):.{precision}g}j".replace("j-", "-j")
        return imag_str if c.imag > 0 else f"-{imag_str}"
    return f"({c.real:.{precision}g}{c.imag:+.{precision}g}j)".replace("+-","-")

def _format_number_as_aop(num: Union[Decimal, complex, float, int], base: int, get_letter: Callable, precision: int, allow_squash: bool = False, is_coeff_formatting: bool = False) -> str:
    if isinstance(num, complex):
        if not cmath.isclose(num.imag, 0):
            return _complex_to_str(num, precision)
        num_decimal = Decimal(str(num.real))
    elif isinstance(num, (float, int)):
        num_decimal = Decimal(str(num))
    else:
        num_decimal = num

    if not num_decimal.is_finite(): return str(num_decimal)
    if num_decimal.is_zero(): return "0"

    # Priority 1: Direct letter representation (e.g., 2 -> b)
    # Only apply if not formatting a coefficient that happens to be in the 1-50 range.
    if not is_coeff_formatting and num_decimal == num_decimal.to_integral_value():
        num_int = int(num_decimal)
        if 1 <= num_int <= 50:
            if letter := get_letter(num_int):
                return letter

    # Priority 2: Coefficient-Letter representation (e.g., 2000 -> 2c)
    if num_decimal == num_decimal.to_integral_value():
        num_int = int(num_decimal)
        for L_raw_exp in sorted(EXPONENT_TO_LETTER_MAP.keys(), reverse=True):
            if L_raw_exp <= 0: continue
            letter_char = get_letter(L_raw_exp)
            try:
                letter_value = Decimal(base) ** L_raw_exp
                if not letter_value.is_zero() and num_int % letter_value == 0:
                    coeff = int(num_int // letter_value) # Use integer division
                    if coeff == 1: return letter_char
                    # Pass is_coeff_formatting=True to prevent '2' becoming 'b' in '2c'
                    formatted_coeff = _format_number_as_aop(coeff, base, get_letter, precision, allow_squash=False, is_coeff_formatting=True)
                    return f"{formatted_coeff}{letter_char}"
            except Exception: continue

    # Priority 3: "Squashing" into a^... form for perfect powers of the base.
    if allow_squash and num_decimal > 0:
        try: # Use logs to find the exponent
            exponent = num_decimal.log10() / Decimal(base).log10()
            if abs(exponent - exponent.to_integral_value(rounding=decimal.ROUND_HALF_UP)) < Decimal("1e-50"):
                exp_int = exponent.to_integral_value(rounding=decimal.ROUND_HALF_UP)
                # When squashing, the new exponent can itself be squashed or be a coeff-letter.
                exp_str = _format_number_as_aop(exp_int, base, get_letter, precision, allow_squash=True, is_coeff_formatting=False)
                return f"a^({exp_str})" if any(c in exp_str for c in ' *()+') else f"a^{exp_str}"
        except Exception: pass

    # Priority 4: Fallback to plain string representation for non-integer numbers or unformattable integers
    return _complex_to_str(complex(num_decimal), precision)

def format_term(term: AoPTerm, base: int, get_letter: Callable, precision: int) -> str:
    coeff_str = _complex_to_str(term.coeff, precision)

    # Case 1: Term is a simple number (exponent is effectively 0)
    # Example: 2000 -> "2c", or 100 -> "b" (if base=10 and 100 itself is requested, not as an exponent of 'a')
    if isinstance(term.exponent, (int, float, Decimal, complex)) and complex(term.exponent) == 0:
        # Format the coefficient itself as an AoP number. Allow squashing if it's a perfect power of base.
        return _format_number_as_aop(term.coeff, base, get_letter, precision, allow_squash=True, is_coeff_formatting=False)

    # Case 2: Term is of the form Coeff * base^Exponent (where Exponent is not 0)
    # Example: Term(coeff=2, exponent=100) -> "2*a^b" (for base 10)
    # Example: Term(coeff=1, exponent=2000) -> "a^2c" (for base 10)
    exp_str = ""
    if isinstance(term.exponent, AoPValue):
        # This is tricky. If the exponent is an AoPValue, its string representation is already handled.
        exp_str = format_output(term.exponent, base, get_letter, OutputFormatMode.AOP, precision)
        if len(term.exponent.terms) > 1 or any(c in exp_str for c in ' *()+'):
            exp_str = f"({exp_str})"
    else: # Exponent is a number
        # Format the exponent part.
        # If coeff is 1 (it's an 'a^exponent_val' term), allow squashing of exponent_val.
        # e.g., for a^10000 (coeff=1, exp=10000), 10000 can become a^d. Result: a^(a^d)
        # For 2*a^2000 (coeff=2, exp=2000), 2000 becomes 2c. Result: 2*a^2c
        can_squash_exponent = cmath.isclose(term.coeff, 1.0)
        exp_str = _format_number_as_aop(term.exponent, base, get_letter, precision, allow_squash=can_squash_exponent, is_coeff_formatting=False)

    if coeff_str == "1": return f"a^{exp_str}"
    if coeff_str == "-1": return f"-a^{exp_str}"

    # Default for Coeff * base^Exponent (where Coeff is not 1 or -1)
    return f"{coeff_str}*a^{exp_str}"

def format_output(value: AoPValue, base: int, get_letter: Callable, mode: OutputFormatMode, precision: int) -> str:
    if not value.terms: return "0"

    if mode == OutputFormatMode.AUTO and len(value.terms) == 1:
        term = value.terms[0]
        # Letter-first rule
        if cmath.isclose(term.coeff, 1.0) and isinstance(term.exponent, (int, float, Decimal, complex)):
            exp_comp = complex(term.exponent)
            if cmath.isclose(exp_comp.imag, 0) and cmath.isclose(exp_comp.real, round(exp_comp.real)):
                exp_int = int(round(exp_comp.real))
                if 1 <= exp_int <= 50:
                    if letter := get_letter(exp_int): return letter
        # Number-first rule
        if isinstance(term.exponent, (int, float, Decimal, complex)) and complex(term.exponent) == 0:
            return _format_number_as_aop(term.coeff, base, get_letter, precision, allow_squash=True)

    if mode in (OutputFormatMode.SCIENTIFIC, OutputFormatMode.NUMERICAL):
        try:
            num = value.to_numerical(base)
            if mode == OutputFormatMode.SCIENTIFIC: return f"{num.real:.{precision}e}" if cmath.isclose(num.imag, 0) else _complex_to_str(num, precision)
            else: return _complex_to_str(num, precision)
        except (OverflowError, PracticalLimitError, NotImplementedError) as e: return f"Error: {e}"

    parts = [format_term(t, base, get_letter, precision) for t in value.terms]
    result = parts[0]
    for part in parts[1:]: result += f" + {part}" if not part.startswith('-') else f" - {part[1:]}"
    return result
