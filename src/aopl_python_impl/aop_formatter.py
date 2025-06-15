# aopl_python_impl/aop_formatter.py

import math
import cmath
from typing import Callable, Dict, Any
from .definitions import ValueTuple, OutputFormatMode
# Import the helper from aop_operations
from .aop_operations import is_symbolic_exponent, MAX_E_FOR_DIRECT_BASE_POWER_CALC

REPRESENTATION_CACHE: Dict[Any, str] = {} # Key can be int or tuple for symbolic exponents

LetterGetter = Callable[[int], str]
# ExponentRepresentationFunc's first arg can be int or symbolic tuple
ExponentRepresentationFunc = Callable[[Any, int, LetterGetter], str]

def _complex_to_str(c: complex, precision: int) -> str:
    if cmath.isclose(c, 0j): return "0"
    if cmath.isclose(c.imag, 0):
        s = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
        return s if s != "-0" else "0"
    if cmath.isclose(c.real, 0):
        sign = "-" if c.imag < 0 else ""
        s_val = f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.')
        return f"{sign}#j" if s_val == "1" else f"{sign}{s_val}#j"
    r_str = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
    i_abs_str = f"{abs(c.imag):.{precision}g}".rstrip('0').rstrip('.')
    op = "-" if c.imag < 0 else "+"
    i_part = "#j" if i_abs_str == "1" else f"{i_abs_str}#j"
    return f"({r_str}{op}{i_part})"

def represent_exponent_as_aop_term(n_or_symbolic_exp: Any, base: int, get_letter_func: LetterGetter) -> str:
    if n_or_symbolic_exp in REPRESENTATION_CACHE: return REPRESENTATION_CACHE[n_or_symbolic_exp]

    if is_symbolic_exponent(n_or_symbolic_exp):
        # It's ("SFP", factor_E1, power_base_E2)
        # Represents factor_E1 * (actual_base_of_calculator ^ power_base_E2)
        sfp_type, factor_E1, power_base_E2 = n_or_symbolic_exp

        factor_E1_repr = represent_exponent_as_aop_term(factor_E1, base, get_letter_func)
        power_base_E2_repr = represent_exponent_as_aop_term(power_base_E2, base, get_letter_func)

        # Format as factor_E1_repr * a^(power_base_E2_repr)
        term2_power_part = f"a^({power_base_E2_repr})" if \
                           any(c in power_base_E2_repr for c in '()^*+- ') or \
                           (power_base_E2_repr.startswith('-') and len(power_base_E2_repr)>1 and not power_base_E2_repr[1:].isdigit()) \
                           else f"a^{power_base_E2_repr}"

        if factor_E1_repr == "1": # factor_E1 was 1
            result = term2_power_part
        else:
            if any(c in factor_E1_repr for c in '()^*+- ') or \
               (factor_E1_repr.startswith('-') and len(factor_E1_repr)>1 and not factor_E1_repr[1:].isdigit()):
                result = f"({factor_E1_repr}) * {term2_power_part}"
            else:
                result = f"{factor_E1_repr} * {term2_power_part}"
        REPRESENTATION_CACHE[n_or_symbolic_exp] = result
        return result

    # Existing logic for n being an integer
    n = n_or_symbolic_exp
    if not isinstance(n, int): return str(n) # Fallback for unexpected types
    if n == 0: return "0"

    sign = ""
    original_n_for_cache = n
    if n < 0:
        sign = "-"
        n = abs(n)

    if 1 <= n <= 25: # Direct letter
        result = sign + get_letter_func(n)
        REPRESENTATION_CACHE[original_n_for_cache] = result
        return result

    coeff_part = n
    power_part_val = 0
    if n > 0 and base > 1:
        while coeff_part > 0 and coeff_part % base == 0:
            coeff_part //= base
            power_part_val += 1

    if coeff_part == 1: # n = base^power_part_val
        power_val_repr = represent_exponent_as_aop_term(power_part_val, base, get_letter_func)
        is_complex_repr = any(c in power_val_repr for c in '()^*+- ') or \
                          (power_val_repr.startswith('-') and len(power_val_repr) > 1 and not power_val_repr[1:].isdigit()) or \
                          (not power_val_repr.isalnum() and power_val_repr != "#j" and not power_val_repr.startswith('a^'))
                          # also check if it's already like a^k

        if is_complex_repr and not (power_val_repr.startswith('(') and power_val_repr.endswith(')')) and not power_val_repr.startswith('a^'):
             result = f"a^({power_val_repr})"
        elif power_val_repr.startswith('a^') and is_complex_repr : # e.g. a^(a^(2c))
             result = f"a^({power_val_repr})"
        else: # Simple letter, number, or already a^something
             result = f"a^{power_val_repr}"
    else: # n is composite or not a power of base
        coeff_repr = str(coeff_part)
        if power_part_val == 0:
            result = coeff_repr
        else:
            power_word_parts = []
            temp_power = power_part_val
            for p_letter_val in range(25, 0, -1):
                count, temp_power = divmod(temp_power, p_letter_val)
                if count > 0:
                    power_word_parts.append(get_letter_func(p_letter_val) * count)
            power_word = "".join(sorted(power_word_parts))
            result = f"{coeff_repr}{power_word}"

    final_result = sign + result
    REPRESENTATION_CACHE[original_n_for_cache] = final_result
    return final_result

def _format_aop_symbolic(value: ValueTuple, base: int, get_letter_func: LetterGetter, represent_exponent_func: ExponentRepresentationFunc) -> str:
    REPRESENTATION_CACHE.clear()
    coeff_val, expon_repr = value # expon_repr can be int or SymbolicExponent

    if cmath.isclose(abs(coeff_val.real), 1.0) and cmath.isclose(coeff_val.imag, 0):
        sign = "-" if coeff_val.real < 0 else ""
        if not is_symbolic_exponent(expon_repr) and expon_repr == 0: return f"{sign}1"
        return sign + represent_exponent_func(expon_repr, base, get_letter_func)

    coeff_str = _complex_to_str(coeff_val, 10)
    if not is_symbolic_exponent(expon_repr) and expon_repr == 0: return coeff_str

    exp_symbolic_part = represent_exponent_func(expon_repr, base, get_letter_func)
    return f"{coeff_str} * {exp_symbolic_part}"

def format_output(value: ValueTuple, base: int, get_letter_func: LetterGetter, represent_exponent_func: ExponentRepresentationFunc, mode: OutputFormatMode, normalize_func, precision: int = 10) -> str:
    coeff, expon_repr = value
    if cmath.isclose(coeff, 0j): return "0"

    # If exponent is already symbolic, cannot do numerical evaluation.
    if is_symbolic_exponent(expon_repr):
        if mode == OutputFormatMode.AOP or mode == OutputFormatMode.AUTO:
            return _format_aop_symbolic(value, base, get_letter_func, represent_exponent_func)
        else: # SCI, NUM for a symbolic exponent should still show its symbolic AOP form
            # Or indicate that it's symbolic and cannot be shown numerically.
            # For now, show AOP form.
            return _format_aop_symbolic(value, base, get_letter_func, represent_exponent_func)

    # Exponent is an integer, proceed with numerical attempt for relevant modes
    expon_int = expon_repr

    if mode == OutputFormatMode.AOP:
        return _format_aop_symbolic(value, base, get_letter_func, represent_exponent_func)

    try:
        # Threshold for expon_int to prevent attempting base**(hyper-large int)
        # This is for the DISPLAY part. The engine might have already produced a huge int.
        if not isinstance(expon_int, int):
            raise TypeError("Exponent must be an integer for numerical evaluation.")
        if expon_int != 0 and expon_int.bit_length() > MAX_E_FOR_DIRECT_BASE_POWER_CALC * 5: # More aggressive threshold for display
            # (MAX_E_FOR_DIRECT_BASE_POWER_CALC is from aop_operations, used as a rough guide)
            # This check is primarily for base ** expon_int in num_val calculation.
            raise OverflowError(f"Exponent (bit_length {expon_int.bit_length()}) too large for direct numerical display attempt.")

        num_val = coeff * (base ** expon_int)

        if mode == OutputFormatMode.SCIENTIFIC:
            if cmath.isclose(num_val.imag, 0): return f"{num_val.real:.{precision}e}"
            return f"({num_val.real:.{precision}e} + {num_val.imag:.{precision}e}j)"

        return _complex_to_str(num_val, precision) # For AUTO and NUMERICAL
    except (OverflowError, ValueError, KeyboardInterrupt) as e:
        return _format_aop_symbolic(value, base, get_letter_func, represent_exponent_func)
