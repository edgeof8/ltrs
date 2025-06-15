# aopl_python_impl/aop_formatter.py

import math
import cmath
from .definitions import ValueTuple, OutputFormatMode, EXPONENT_TO_LETTER_MAP
from .interfaces import LetterGetter, ExponentRepresentationFunc

def _complex_to_str(c: complex, precision: int) -> str:
    if cmath.isclose(c, 0j): return "0"
    if cmath.isclose(c.imag, 0):
        s = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
        return s if s != "-0" else "0"
    if cmath.isclose(c.real, 0):
        sign = "-" if c.imag < 0 else ""
        s = f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.')
        return f"{sign}#j" if s == "1" else f"{sign}{s}#j"
    r, i = f"{c.real:.{precision}g}".rstrip('0').rstrip('.'), f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.')
    op = "-" if c.imag < 0 else "+"
    i_part = "#j" if i == "1" else f"{i}#j"
    return f"({r}{op}{i_part})"

def represent_exponent_as_aop_term(exponent_value: int, base: int, get_letter_func: LetterGetter) -> str:
    if not isinstance(exponent_value, int) or base <= 1:
        return str(exponent_value)

    if 1 <= exponent_value <= 26:
        return get_letter_func(exponent_value)

    # Use logarithms to find the largest power-of-base factor
    try:
        log_of_exp = math.log(exponent_value, base)
        # Find the largest letter whose power is <= log_of_exp
        largest_letter_exp = int(math.floor(log_of_exp))

        if largest_letter_exp > 0:
            power_of_base = base ** largest_letter_exp
            if power_of_base != 0 and exponent_value % power_of_base == 0:
                coeff_val = exponent_value // power_of_base
                letter_char = get_letter_func(largest_letter_exp)
                if letter_char:
                    if coeff_val == 1: return letter_char
                    # Do not recurse, just return the coefficient
                    return f"{coeff_val}{letter_char}"
    except (ValueError, OverflowError):
        pass # Fallback to string if log fails

    return str(exponent_value)


def format_output(value: ValueTuple, base: int, get_letter_func: LetterGetter, represent_exponent_func: ExponentRepresentationFunc, mode: OutputFormatMode, normalize_func, precision: int = 10) -> str:
    coeff, expon = value
    if cmath.isclose(coeff, 0j): return "0"

    if mode in [OutputFormatMode.AOP, OutputFormatMode.AUTO]:
        if cmath.isclose(coeff, 1.0):
            if expon == 0: return "1"
            formatted_exp = represent_exponent_as_aop_term(expon, base, get_letter_func)
            if len(formatted_exp) <= 2 and formatted_exp.lstrip('-').isalpha():
                return formatted_exp
            return f"a^{formatted_exp}"

        if cmath.isclose(coeff, -1.0):
            if expon == 0: return "-1"
            formatted_exp = represent_exponent_as_aop_term(expon, base, get_letter_func)
            if len(formatted_exp) <= 2 and formatted_exp.lstrip('-').isalpha():
                return f"-{formatted_exp}"
            return f"-a^{formatted_exp}"

        coeff_str = _complex_to_str(coeff, precision)
        if expon == 0: return coeff_str
        exp_str = represent_exponent_as_aop_term(expon, base, get_letter_func)
        return f"{coeff_str} * {exp_str}"

    try:
        num_val = coeff * (base ** expon)
        return _complex_to_str(num_val, precision)
    except OverflowError:
        return format_output(value, base, get_letter_func, represent_exponent_func, OutputFormatMode.AOP, normalize_func, precision)
