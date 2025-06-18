# aopl_python_impl/aop_formatter.py
import math, cmath, decimal
from decimal import Decimal, getcontext
from typing import Callable, Union, TYPE_CHECKING
# Import PracticalLimitError from definitions, and other necessary items
from .definitions import OutputFormatMode, EXPONENT_TO_LETTER_MAP, PracticalLimitError

if TYPE_CHECKING:
    from .aop_value import AoPValue, AoPTerm # Moved here for type hinting only

getcontext().prec = 100

# ... (rest of _complex_to_str is unchanged) ...
def _complex_to_str(c: complex, precision: int) -> str:
    if cmath.isclose(c.imag, 0):
        real_part = c.real
        if cmath.isclose(real_part, round(real_part)):
            if abs(real_part) < 1e18:
                return str(int(round(real_part)))
        if abs(real_part) > 1e15 or (abs(real_part) < 1e-4 and real_part != 0):
            return f"{real_part:.{precision}e}"
        formatted_g = f"{real_part:.{precision}g}"
        if 'e' in formatted_g.lower():
            return formatted_g
        return formatted_g.rstrip('0').rstrip('.')

    if cmath.isclose(c.real, 0):
        imag_part = c.imag
        if cmath.isclose(abs(imag_part), 1.0):
            return "j" if imag_part > 0 else "-j"
        imag_val_str = ""
        if cmath.isclose(imag_part, round(imag_part)):
             if abs(imag_part) < 1e18:
                imag_val_str = str(int(round(imag_part)))
        if not imag_val_str:
            if abs(imag_part) > 1e15 or (abs(imag_part) < 1e-4 and imag_part != 0):
                imag_val_str = f"{imag_part:.{precision}e}"
            else:
                formatted_g = f"{imag_part:.{precision}g}"
                if 'e' in formatted_g.lower():
                    imag_val_str = formatted_g
                else:
                    imag_val_str = formatted_g.rstrip('0').rstrip('.')
        return f"{imag_val_str}j"

    r_str = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
    imag_sign = '+' if c.imag > 0 else '-'
    imag_abs = abs(c.imag)

    imag_val_str = ""
    if cmath.isclose(imag_abs, 1.0):
        imag_str = "j"
    else:
        if cmath.isclose(imag_abs, round(imag_abs)):
            if abs(imag_abs) < 1e18:
                 imag_val_str = str(int(round(imag_abs)))
        if not imag_val_str:
            if abs(imag_abs) > 1e15 or (abs(imag_abs) < 1e-4 and imag_abs != 0):
                imag_val_str = f"{imag_abs:.{precision}e}"
            else:
                formatted_g = f"{imag_abs:.{precision}g}"
                if 'e' in formatted_g.lower():
                    imag_val_str = formatted_g
                else:
                    imag_val_str = formatted_g.rstrip('0').rstrip('.')
        imag_str = f"{imag_val_str}j"

    return f"({r_str}{imag_sign}{imag_str})"


def _format_numeric_exponent(num: Union[Decimal, complex, float, int], base: int, get_letter: Callable, precision: int) -> str:
    # DEBUG PRINT: Initial entry
    # print(f"DEBUG: _format_numeric_exponent called with num={num} (type {type(num)}), base={base}")

    if isinstance(num, complex):
        if not cmath.isclose(num.imag, 0):
            # print(f"DEBUG: _format_numeric_exponent: num is complex with imag part, returning _complex_to_str")
            return _complex_to_str(num, precision)
        num_decimal = Decimal(num.real)
    elif isinstance(num, Decimal):
        num_decimal = num
    elif isinstance(num, float):
        num_decimal = Decimal(str(num))
    elif isinstance(num, int):
        num_decimal = Decimal(num)
    else:
        raise TypeError(f"Unsupported type for _format_numeric_exponent: {type(num)}")

    # print(f"DEBUG: _format_numeric_exponent: num_decimal={num_decimal} (type {type(num_decimal)})")

    if not num_decimal.is_finite():
        # print(f"DEBUG: _format_numeric_exponent: num_decimal not finite, returning _complex_to_str")
        return _complex_to_str(complex(num_decimal), precision)

    if num_decimal.is_zero():
        # print(f"DEBUG: _format_numeric_exponent: num_decimal is zero, returning '0'")
        return "0"

    is_integral = False
    try:
        num_decimal.to_integral_exact(rounding=decimal.ROUND_FLOOR)
        is_integral = True
    except decimal.Inexact:
        is_integral = False

    # print(f"DEBUG: _format_numeric_exponent: is_integral={is_integral}")

    if not is_integral:
        # print(f"DEBUG: _format_numeric_exponent: not integral, returning _complex_to_str")
        return _complex_to_str(complex(num_decimal), precision)

    # At this point, num_decimal is an integer-valued Decimal.
    num_int_for_letter_check = -1 # Sentinel
    try:
        # Limit int conversion to a practical range for direct letter mapping
        if num_decimal.compare(Decimal('-1E18')) == 1 and num_decimal.compare(Decimal('1E18')) == -1: # -1E18 < num_decimal < 1E18
             num_int_for_letter_check = int(num_decimal)
    except (OverflowError, ValueError):
        pass # Will remain -1, won't match 1-50 range or will be caught by magnitude check

    # MOVED DEBUG PRINT HERE, before the conditional block
    print(f"DEBUG: fmt_num_exp: num_decimal='{num_decimal}', num_int_for_letter_check='{num_int_for_letter_check}'")
    if num_int_for_letter_check != -1 : # Only attempt get_letter if conversion to int was successful
        letter_result_debug = get_letter(num_int_for_letter_check)
        print(f"DEBUG: fmt_num_exp: get_letter({num_int_for_letter_check}) got: '{letter_result_debug}' (type: {type(letter_result_debug)})")
        if 1 <= num_int_for_letter_check <= 50:
            if letter_result_debug and isinstance(letter_result_debug, str) and letter_result_debug.strip(): # Check if it's a non-empty string
                # print(f"DEBUG: fmt_num_exp: Returning direct letter: '{letter_result_debug}'")
                return letter_result_debug

    # print(f"DEBUG: fmt_num_exp: Did not return direct letter. Proceeding to Coeff*Letter search or fallback for '{num_decimal}'.")

    for L_raw_exp in sorted(EXPONENT_TO_LETTER_MAP.keys(), reverse=True):
        if L_raw_exp <= 0: continue
        letter_char = get_letter(L_raw_exp) # This get_letter is for the L_raw_exp (e.g. 29 -> D)
        if not letter_char: continue

        try:
            letter_actual_value = Decimal(base) ** Decimal(L_raw_exp)
            if letter_actual_value.is_zero(): continue
            if abs(num_decimal) < abs(letter_actual_value) and not num_decimal.is_zero() : continue

            if num_decimal % letter_actual_value == 0:
                coeff_dec = num_decimal / letter_actual_value
                is_coeff_integral = False
                try:
                    coeff_dec.to_integral_exact(rounding=decimal.ROUND_FLOOR)
                    is_coeff_integral = True
                except decimal.Inexact:
                    is_coeff_integral = False

                if is_coeff_integral:
                    coeff_int = int(coeff_dec)
                    if coeff_int == 1:
                        # print(f"DEBUG: fmt_num_exp: Coeff*Letter returning letter_char '{letter_char}' for num_decimal '{num_decimal}'")
                        return letter_char
                    if coeff_int != 0:
                        # print(f"DEBUG: fmt_num_exp: Coeff*Letter returning '{str(coeff_int)}{letter_char}' for num_decimal '{num_decimal}'")
                        return f"{str(coeff_int)}{letter_char}"
        except (decimal.Overflow, decimal.InvalidOperation, ValueError):
            continue
        except Exception:
            continue

    # print(f"DEBUG: fmt_num_exp: Fallback, returning _complex_to_str for '{num_decimal}'")
    return _complex_to_str(complex(num_decimal), precision)


# ... (rest of format_term and format_output are unchanged) ...
def format_term(term: 'AoPTerm', base: int, get_letter: Callable, precision: int) -> str:
    # ILLUSTRATIVE function. Primary formatting is AoPTerm.to_str() in aop_value.py.
    if not (hasattr(term, 'coeff') and hasattr(term, 'exponent')):
        return "[Error: Invalid term structure for format_term]"

    coeff_str = _complex_to_str(term.coeff, precision)

    is_exp_zero = False
    if isinstance(term.exponent, (int, float, Decimal, complex)):
        try:
            if cmath.isclose(complex(term.exponent), 0): is_exp_zero = True
        except TypeError: pass

    if is_exp_zero: return coeff_str

    exp_str = ""
    is_aop_value_exponent = hasattr(term.exponent, 'terms') and callable(getattr(term.exponent, 'to_str', None))

    if is_aop_value_exponent:
        exp_obj = term.exponent # type: 'AoPValue'
        exp_str = format_output(exp_obj, base, get_letter, OutputFormatMode.AOP, precision)
        if len(exp_obj.terms) > 1 or any(c in exp_str for c in ' *()+^'): # Check original AoPValue structure
            exp_str = f"({exp_str})"
    elif isinstance(term.exponent, (Decimal, complex, float, int)):
        exp_str = _format_numeric_exponent(term.exponent, base, get_letter, precision)
    else:
        return f"[Error: Unknown exponent type '{type(term.exponent)}' in format_term]"

    if coeff_str == "1": return f"a^{exp_str}"
    if coeff_str == "-1": return f"-a^{exp_str}"

    if exp_str.isalnum() or \
       (exp_str.startswith('-') and exp_str[1:].isalnum()) or \
       (exp_str.startswith('+') and exp_str[1:].isalnum()):
        return f"{coeff_str}a^{exp_str}"
    return f"{coeff_str}*a^{exp_str}"

def format_output(value: 'AoPValue', base: int, get_letter: Callable, mode: OutputFormatMode, precision: int) -> str:
    # ILLUSTRATIVE function. Primary formatting is AoPValue.to_str() in aop_value.py.
    if not (hasattr(value, 'terms') and hasattr(value, 'to_numerical')):
         return "[Error: Invalid value structure for format_output]"
    if not value.terms: return "0"

    if mode == OutputFormatMode.AUTO and len(value.terms) == 1:
        term = value.terms[0] # type: 'AoPTerm'
        if not (hasattr(term, 'coeff') and hasattr(term, 'exponent')):
            return "[Error: Invalid term structure in AUTO mode format_output]"

        if cmath.isclose(term.coeff, 1.0) and isinstance(term.exponent, (int, float, Decimal, complex)):
            exp_comp = complex(term.exponent)
            if cmath.isclose(exp_comp.imag, 0) and cmath.isclose(exp_comp.real, round(exp_comp.real)):
                exp_int = int(round(exp_comp.real))
                if 1 <= exp_int <= 50:
                    if letter := get_letter(exp_int): return letter

        is_exp_zero = False
        if isinstance(term.exponent, (int, float, Decimal, complex)):
            if cmath.isclose(complex(term.exponent), 0): is_exp_zero = True
        if is_exp_zero: return _complex_to_str(term.coeff, precision)

    if mode in (OutputFormatMode.SCIENTIFIC, OutputFormatMode.NUMERICAL):
        try:
            num = value.to_numerical(base)
            if mode == OutputFormatMode.SCIENTIFIC:
                return f"{num.real:.{precision}e}" if cmath.isclose(num.imag, 0) else _complex_to_str(num, precision)
            else: # NUMERICAL
                return _complex_to_str(num, precision)
        except (OverflowError, PracticalLimitError, NotImplementedError) as e: return f"Error: {e}"

    parts = []
    for t in value.terms: # t is AoPTerm-like
        parts.append(format_term(t, base, get_letter, precision))

    if not parts: return "0"
    result = parts[0]
    for part in parts[1:]:
        result += f" + {part}" if not part.startswith('-') else f" - {part[1:]}"
    return result
