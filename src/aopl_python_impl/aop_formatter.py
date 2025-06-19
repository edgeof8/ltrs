# aopl_python_impl/aop_formatter.py
import math, cmath, decimal
from decimal import Decimal, getcontext
from typing import Callable, Union
from .aop_value import AoPValue, AoPTerm, PracticalLimitError
from .definitions import OutputFormatMode, EXPONENT_TO_LETTER_MAP

getcontext().prec = 200

def _complex_to_str(c: complex, precision: int) -> str:
    # Define a suitable absolute tolerance for checking closeness to zero
    abs_tol_zero = 1e-12 # Adjusted tolerance
    if cmath.isclose(c.imag, 0, abs_tol=abs_tol_zero):
        real_part = c.real
        # For real part, check if it's an integer
        if cmath.isclose(real_part, round(real_part), rel_tol=1e-9, abs_tol=abs_tol_zero): # Use rel_tol for round check
            return str(int(round(real_part)))
        return f"{real_part:.{precision}g}".rstrip('0').rstrip('.')
    if cmath.isclose(c.real, 0, abs_tol=abs_tol_zero) and cmath.isclose(c.imag, 0, abs_tol=abs_tol_zero): return "0"
    if cmath.isclose(c.real, 0, abs_tol=abs_tol_zero):
        # Use #j for the imaginary unit in output
        imag_coeff_str = "" if cmath.isclose(abs(c.imag), 1.0, rel_tol=1e-9, abs_tol=abs_tol_zero) else f"{abs(c.imag):.{precision}g}"
        imag_str = f"{imag_coeff_str}#j"
        return imag_str if c.imag > 0 else f"-{imag_str}"
    # Use #j for the imaginary unit in output
    real_part_str = f"{c.real:.{precision}g}"
    imag_part_str = f"{c.imag:+.{precision}g}#j" # Add #j here
    return f"({real_part_str}{imag_part_str})".replace("+-","-")

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
        num_int = int(num_decimal.to_integral_value(rounding=decimal.ROUND_HALF_UP))
        # If formatting the number 1 as a standalone value (where allow_squash is true,
        # passed from format_term's numeric path), it should be "1".
        # The letter 'a' (for base 10) represents 10^1, not the number 1.
        if num_int == 1 and allow_squash:
            return "1" # Explicitly format the number 1 as "1"
        elif 1 <= num_int <= 50:
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
    # Numeric-First Formatting for individual terms
    try:
        # Attempt to get the full numerical value of the term
        # AoPTerm.to_numerical() uses Decimal for precision
        numerical_value_of_term = term.to_numerical(base)
        # If successful, format this single numerical value using the AoP rules
        # allow_squash=True because this is the term's complete value
        return _format_number_as_aop(numerical_value_of_term, base, get_letter, precision, allow_squash=True, is_coeff_formatting=False)
    except PracticalLimitError: # Catches OverflowError from to_numerical if exponent is too large/symbolic
        # Symbolic Fallback Formatting if term cannot be represented as a single number
        coeff_str = _complex_to_str(term.coeff, precision)
        exp_str = ""
        if isinstance(term.exponent, AoPValue):
            # The exponent is already an AoPValue (symbolic structure)
            exp_str = format_output(term.exponent, base, get_letter, OutputFormatMode.AOP, precision)
            # Add parentheses if the exponent's string form is complex
            if len(term.exponent.terms) > 1 or any(c in exp_str for c in ' *()+^-'): # Check for operators too
                exp_str = f"({exp_str})"
        else: # Exponent is a simple number (but couldn't be evaluated with coeff above, e.g. coeff is complex, or exp is complex)
              # Or, term.to_numerical failed for other reasons but exponent is simple.
            # Format the exponent number. Allow squashing if coeff is 1 (e.g. a^10000 -> a^(a^d))
            # is_coeff_formatting=False because this is an exponent value.
            can_squash_exponent = cmath.isclose(term.coeff, 1.0) and cmath.isclose(term.coeff.imag,0)
            exp_str = _format_number_as_aop(term.exponent, base, get_letter, precision, allow_squash=can_squash_exponent, is_coeff_formatting=False)

        if cmath.isclose(term.coeff, 1.0) and cmath.isclose(term.coeff.imag,0): return f"a^{exp_str}"
        if cmath.isclose(term.coeff, -1.0) and cmath.isclose(term.coeff.imag,0): return f"-a^{exp_str}"

        # If exponent is 0 for a symbolic/complex coefficient, it should be just the coefficient string
        if isinstance(term.exponent, (Decimal, complex, int, float)) and complex(term.exponent) == 0:
             return coeff_str # e.g. for a complex coefficient like (1+2#j) * base^0

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
