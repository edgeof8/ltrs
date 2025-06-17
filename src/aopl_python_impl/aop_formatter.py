import math
import cmath
from decimal import Decimal
from typing import Callable, Union, Optional, Tuple
from .aop_value import AoPValue, PracticalLimitError
from .definitions import OutputFormatMode, LETTER_TO_EXPONENT_MAP as LE_MAP, EXPONENT_TO_LETTER_MAP as EL_MAP

DEBUG_AOP_FORMATTER = False

LetterGetter = Callable[[int], str]

def _complex_to_str(c: complex, precision: int) -> str:
    # This function is now considered correct and stable. No changes needed.
    is_real_nan = cmath.isnan(c.real)
    is_imag_nan = cmath.isnan(c.imag)
    is_real_inf = cmath.isinf(c.real)
    is_imag_inf = cmath.isinf(c.imag)

    if is_real_nan or is_imag_nan:
        if is_real_nan and is_imag_nan: return "(nan+nanj)"
        if is_real_nan:
            if is_imag_inf:
                imag_sign = '+' if c.imag >= 0 else ''
                return f"(nan{imag_sign}{'infj' if c.imag > 0 else '-infj'})"
            else:
                return f"(nan{'+' if c.imag >= 0 else ''}{c.imag:.{precision}g}j)"
        if is_imag_nan:
            if is_real_inf:
                return f"({'inf' if c.real > 0 else '-inf'}+nanj)"
            else:
                return f"({c.real:.{precision}g}+nanj)"
        return "NaN"

    if is_real_inf or is_imag_inf:
        real_str = "inf" if c.real > 0 else "-inf" if is_real_inf else f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
        if real_str == "-0": real_str = "0"

        imag_sign_char = "+" if c.imag >= 0 else "-"
        abs_imag_val = abs(c.imag)
        imag_val_str = "inf" if is_imag_inf else f"{abs_imag_val:.{precision}g}".rstrip('0').rstrip('.')
        if cmath.isclose(abs_imag_val, 1.0) and imag_val_str == "1": imag_val_str = ""

        if is_real_inf and not is_imag_inf and cmath.isclose(c.imag, 0): return real_str
        if is_imag_inf and not is_real_inf and cmath.isclose(c.real, 0): return f"{imag_sign_char.strip('+')}{imag_val_str}j"
        return f"({real_str}{imag_sign_char}{imag_val_str}j)"

    if cmath.isclose(c, 0j): return "0"
    if cmath.isclose(c.imag, 0): return f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
    if cmath.isclose(c.real, 0):
        imag_str = "j" if cmath.isclose(abs(c.imag), 1.0) else f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.') + "j"
        return f"{'-' if c.imag < 0 else ''}{imag_str}"

    r_str = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
    imag_str = "j" if cmath.isclose(abs(c.imag), 1.0) else f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.') + "j"
    op_char = "+" if c.imag > 0 else "-"
    return f"({r_str}{op_char}{imag_str})"


def _represent_numeric_exponent_as_coeff_letter_string(exp_int: int, base: int) -> Optional[str]:
    # This function is now considered correct and stable. No changes needed.
    if exp_int <= 0: return None
    best_representation: Optional[str] = None
    original_len = max(1, len(str(exp_int)))
    for letter_aop_exp_val in sorted(EL_MAP.keys(), reverse=True):
        if letter_aop_exp_val <= 0: continue
        letter_char = EL_MAP[letter_aop_exp_val]
        try:
            letter_numerical_value = base ** letter_aop_exp_val
        except OverflowError:
            continue
        if letter_numerical_value > exp_int: continue
        if exp_int % letter_numerical_value == 0:
            coeff_K = exp_int // letter_numerical_value
            if coeff_K > 0:
                current_repr = f"{coeff_K}{letter_char}" if coeff_K != 1 else letter_char
                if best_representation is None or len(current_repr) < len(best_representation) or \
                   (len(current_repr) == len(best_representation) and letter_aop_exp_val > LE_MAP.get(best_representation[-1], 0)):
                    best_representation = current_repr
    if best_representation and len(best_representation) < original_len:
        return best_representation
    return None


def format_output(value: AoPValue, base: int, get_letter: LetterGetter, mode: OutputFormatMode, precision: int) -> str:
    if DEBUG_AOP_FORMATTER: print(f"[DEBUG format_output ENTRY] value: {value}, mode: {mode}")
    from .aop_operations import simplify_value

    val = simplify_value(value, base)
    if DEBUG_AOP_FORMATTER and val is not value:
        print(f"[DEBUG format_output AFTER_SIMPLIFY] original: {value}, simplified_val: {val}")

    if cmath.isclose(val.coeff, 0j): return "0"
    if cmath.isnan(val.coeff.real) or cmath.isnan(val.coeff.imag) or \
       cmath.isinf(val.coeff.real) or cmath.isinf(val.coeff.imag):
        coeff_str = _complex_to_str(val.coeff, precision)
        if val.is_numeric() and val.exponent == 0: return coeff_str
        exponent_value = val.exponent if isinstance(val.exponent, AoPValue) else AoPValue(1.0, val.exponent)
        exp_part_str = format_output(exponent_value, base, get_letter, OutputFormatMode.AOP, precision)
        if exp_part_str in ("1", "0"): return coeff_str
        return f"{coeff_str}*{exp_part_str}"

    if not val.is_numeric():
        if DEBUG_AOP_FORMATTER: print(f"[DEBUG format_output] Path: RECURSIVE value: {val}")
        exponent_value = val.exponent
        assert isinstance(exponent_value, AoPValue)
        exponent_str = format_output(exponent_value, base, get_letter, OutputFormatMode.AOP, precision)
        if DEBUG_AOP_FORMATTER: print(f"[DEBUG format_output] RECURSIVE exponent formatted to: '{exponent_str}'")

        # --- REVISED PARENTHESIZING LOGIC ---
        # An exponent needs parentheses if it contains an operator and is not already wrapped.
        is_expression = any(op in exponent_str for op in ['+', '-', '*', '/', '^'])
        is_already_wrapped = exponent_str.startswith('(') and exponent_str.endswith(')')

        if is_expression and not is_already_wrapped:
             exponent_str = f"({exponent_str})"
        # --- END REVISED LOGIC ---

        if cmath.isclose(val.coeff, 1.0):
            return f"a^{exponent_str}"
        else:
            coeff_str = _complex_to_str(val.coeff, precision)
            return f"{coeff_str}*a^{exponent_str}"

    assert isinstance(val.exponent, (complex, Decimal))

    is_exponent_purely_real_int = False
    exponent_as_precise_int = Decimal(0)

    if isinstance(val.exponent, Decimal):
        if val.exponent == val.exponent.to_integral_value():
            is_exponent_purely_real_int = True
            exponent_as_precise_int = val.exponent.to_integral_value()
    elif isinstance(val.exponent, complex):
        if cmath.isclose(val.exponent.imag, 0) and cmath.isclose(val.exponent.real, round(val.exponent.real)):
            is_exponent_purely_real_int = True
            try:
                exponent_as_precise_int = Decimal(int(round(val.exponent.real)))
            except (OverflowError, TypeError):
                is_exponent_purely_real_int = False

    if mode == OutputFormatMode.AOP:
        coeff_str = _complex_to_str(val.coeff, precision)
        is_exp_zero = (isinstance(val.exponent, Decimal) and val.exponent.is_zero()) or \
                      (isinstance(val.exponent, complex) and cmath.isclose(val.exponent, 0j))
        if is_exp_zero: return coeff_str

        exp_part_str = ""
        if is_exponent_purely_real_int:
            exp_int = int(exponent_as_precise_int)
            letter = get_letter(exp_int)
            if letter:
                exp_part_str = letter
            else:
                factored_exp_str = _represent_numeric_exponent_as_coeff_letter_string(exp_int, base)
                if factored_exp_str:
                    exp_part_str = f"a^{factored_exp_str}"
                else:
                    exp_part_str = f"a^{exp_int}"
        else:
            # --- REVISED NUMERIC FORMATTING ---
            # _complex_to_str will add parentheses if needed (e.g. for "3+4j").
            # Do not add a second, redundant layer of parentheses here.
            exp_str_repr = _complex_to_str(val.exponent, precision)
            exp_part_str = f"a^{exp_str_repr}"
            # --- END REVISED LOGIC ---

        if cmath.isclose(val.coeff, 1.0):
            return exp_part_str
        else:
            return f"{coeff_str}*{exp_part_str}"

    if mode == OutputFormatMode.AUTO:
        if cmath.isclose(val.coeff, 1.0) and is_exponent_purely_real_int:
            letter = get_letter(int(exponent_as_precise_int))
            if letter: return letter
        try:
            num_val = val.to_numerical(base)
            s_num_val = _complex_to_str(num_val, precision)
            is_nan_or_inf = "nan" in s_num_val.lower() or "inf" in s_num_val.lower()
            is_complex_fmt = '(' in s_num_val or 'j' in s_num_val.lower()
            if not is_nan_or_inf and not is_complex_fmt:
                is_scientific = 'e' in s_num_val.lower()
                if (is_scientific and len(s_num_val) < 15) or (not is_scientific and len(s_num_val) < 10):
                    return s_num_val
        except (PracticalLimitError, OverflowError):
            pass
        return format_output(val, base, get_letter, OutputFormatMode.AOP, precision)

    if mode == OutputFormatMode.NUMERICAL or mode == OutputFormatMode.SCIENTIFIC:
        try:
            num_val = val.to_numerical(base)
            return _complex_to_str(num_val, precision)
        except OverflowError:
            return format_output(val, base, get_letter, OutputFormatMode.AOP, precision)

    return "[FORMATTING_ERROR_MODE_NOT_HANDLED]"
