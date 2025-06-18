# aopl_python_impl/aop_formatter.py
import math, cmath
from decimal import Decimal
from typing import Callable, Optional, Union, List
from .aop_value import AoPValue, AoPTerm, PracticalLimitError
from .definitions import OutputFormatMode, LETTER_TO_EXPONENT_MAP as LE_MAP, EXPONENT_TO_LETTER_MAP as EL_MAP

def _complex_to_str(c: complex, precision: int) -> str:
    # This function is stable and correct
    if cmath.isclose(c.imag, 0):
        real_part = c.real
        if cmath.isclose(real_part, round(real_part)): return str(int(round(real_part)))
        if abs(real_part) > 1e15: return f"{real_part:.{precision}e}"
        return f"{real_part:.{precision}g}".rstrip('0').rstrip('.')
    if cmath.isclose(c, 0j): return "0"
    if cmath.isclose(c.real, 0):
        imag_str = "j" if cmath.isclose(abs(c.imag), 1.0) else f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.') + "j"
        return f"{'-' if c.imag < 0 else ''}{imag_str}"
    r_str = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
    imag_str = "j" if cmath.isclose(abs(c.imag), 1.0) else f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.') + "j"
    return f"({r_str}{'+' if c.imag > 0 else '-'}{imag_str})"

def _represent_numeric_exponent(exp: Union[Decimal, complex], base: int, get_letter: Callable[[int], str], precision: int) -> str:
    is_int_real = (isinstance(exp, Decimal) and exp == exp.to_integral_value()) or \
                  (isinstance(exp, complex) and cmath.isclose(exp.imag, 0) and cmath.isclose(exp.real, round(exp.real)))
    if is_int_real:
        exp_int = int(round(exp.real)) if isinstance(exp, complex) else int(exp)
        if letter := get_letter(exp_int): return letter
        return f"a^{exp_int}"
    return f"a^({_complex_to_str(complex(exp), precision)})"

def format_term(term: AoPTerm, base: int, get_letter: Callable[[int], str], mode: OutputFormatMode, precision: int) -> str:
    is_coeff_one = cmath.isclose(term.coeff, 1.0)
    coeff_str = "" if is_coeff_one else _complex_to_str(term.coeff, precision)

    is_exp_zero = isinstance(term.exponent, (int, float, Decimal, complex)) and term.exponent == 0
    if is_exp_zero:
        return coeff_str or "1"

    exp_str = ""
    if isinstance(term.exponent, AoPValue):
        # Always format exponents symbolically to preserve their structure.
        formatted_inner_exp = format_output(term.exponent, base, get_letter, OutputFormatMode.AOP, precision)
        if any(c in formatted_inner_exp for c in ' +-*/^()'):
             exp_str = f"a^({formatted_inner_exp})"
        else:
             exp_str = f"a^{formatted_inner_exp}"
    else:
        exp_str = _represent_numeric_exponent(term.exponent, base, get_letter, precision)

    if is_coeff_one:
        return exp_str

    # --- FIX: IMPLICIT MULTIPLICATION LOGIC ---
    # If the exponent string represents a "word" (starts with a letter or 'a^'), omit the '*'.
    if exp_str and (exp_str[0].isalpha() or exp_str.startswith('a^')):
        return f"{coeff_str}{exp_str}"

    return f"{coeff_str}*{exp_str}"

def format_output(value: AoPValue, base: int, get_letter: Callable[[int], str], mode: OutputFormatMode, precision: int) -> str:
    if not value.terms: return "0"

    if mode == OutputFormatMode.AUTO and len(value.terms) == 1:
        term = value.terms[0]
        # Only try to make numeric if the exponent is also numeric
        if isinstance(term.exponent, (int, float, Decimal, complex)):
            try:
                num = value.to_numerical(base)
                s_num = _complex_to_str(num, precision)
                if len(s_num) < 15 and '(' not in s_num:
                    # Final check: does the numeric form lose AoP structure?
                    # e.g. 1000 should be 'd', not '1000'.
                    if 'e' not in s_num and (letter := get_letter(int(s_num))):
                        return letter
                    return s_num
            except (OverflowError, PracticalLimitError):
                pass

    parts = []
    for i, term in enumerate(value.terms):
        term_str = format_term(term, base, get_letter, mode, precision)
        if i > 0 and not term_str.startswith('-'):
            parts.append("+")
        parts.append(term_str)

    return " ".join(parts)
