# aopl_python_impl/aop_formatter.py
import math, cmath, decimal
from decimal import Decimal, getcontext
from typing import Callable, Union
from .aop_value import AoPValue, AoPTerm, PracticalLimitError
from .definitions import OutputFormatMode, EXPONENT_TO_LETTER_MAP

getcontext().prec = 100

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

def format_term(term: AoPTerm, base: int, get_letter: Callable, precision: int) -> str:
    coeff_str = _complex_to_str(term.coeff, precision)
    if isinstance(term.exponent, (int, float, Decimal, complex)) and complex(term.exponent) == 0:
        return coeff_str
    exp_str = ""
    if isinstance(term.exponent, AoPValue):
        exp_str = format_output(term.exponent, base, get_letter, OutputFormatMode.AOP, precision)
        if len(term.exponent.terms) > 1 or any(c in exp_str for c in ' *()+'):
            exp_str = f"({exp_str})"
    else:
        exp_comp = complex(term.exponent)
        if cmath.isclose(exp_comp.imag, 0) and cmath.isclose(exp_comp.real, round(exp_comp.real)):
            exp_int = int(round(exp_comp.real))
            if 1 <= exp_int <= 50 and (letter := get_letter(exp_int)):
                exp_str = letter
            else:
                exp_str = str(exp_int)
        else:
            exp_str = _complex_to_str(exp_comp, precision)
    if coeff_str == "1": return f"a^{exp_str}"
    if coeff_str == "-1": return f"-a^{exp_str}"
    if exp_str.isalnum(): return f"{coeff_str}a^{exp_str}"
    return f"{coeff_str}*a^{exp_str}"

def format_output(value: AoPValue, base: int, get_letter: Callable, mode: OutputFormatMode, precision: int) -> str:
    if not value.terms: return "0"
    if mode == OutputFormatMode.AUTO and len(value.terms) == 1:
        term = value.terms[0]
        if cmath.isclose(term.coeff, 1.0) and isinstance(term.exponent, (int, float, Decimal, complex)):
            exp_comp = complex(term.exponent)
            if cmath.isclose(exp_comp.imag, 0) and cmath.isclose(exp_comp.real, round(exp_comp.real)):
                exp_int = int(round(exp_comp.real))
                if 1 <= exp_int <= 50:
                    if letter := get_letter(exp_int): return letter
        if isinstance(term.exponent, (int, float, Decimal, complex)) and complex(term.exponent) == 0:
            return _complex_to_str(term.coeff, precision)
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
