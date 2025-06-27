# aopl_python_impl/aop_formatter.py
from .aop_value import AoPValue
import logging

# We'll add a depth parameter to make the recursive calls easy to read.
_format_depth = 0
# --- NEW: A list to store sub-format messages ---
_sub_format_logs = []

def _format_number_in_base(n: int, base: int) -> str:
    """Converts an integer to its string representation in a given base."""
    if n == 0:
        return "0"
    if base < 2 or base > 36:
        raise ValueError("Base must be between 2 and 36")

    is_negative = n < 0
    if is_negative:
        n = -n

    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = ""
    while n > 0:
        res = digits[n % base] + res
        n //= base

    return "-" + res if is_negative else res

# --- MODIFIED: This is the main recursive formatter, now simplified and corrected ---
def format_as_aop(val: AoPValue, letter_map: dict) -> str:
    """Formats the polynomial into a symbolic letter string."""
    global _format_depth, _sub_format_logs

    is_top_level_call = (_format_depth == 0)
    if is_top_level_call:
        _sub_format_logs = []
        log_format_report_start(repr(val))

    _format_depth += 1

    if not val.poly:
        _format_depth -= 1
        return "0"

    current_base = val.base
    base_symbol = 'a'

    parts = []
    for exp, coeff in sorted(val.poly.items(), reverse=True):
        if coeff == 0: continue

        display_coeff = -coeff if val.is_negative else coeff
        coeff_str = _format_number_in_base(display_coeff, current_base)

        if abs(display_coeff) == 1 and exp != 0:
            coeff_str = "" if display_coeff > 0 else "-"

        if exp == 0:
            exp_str = ""
        elif exp in letter_map:
            exp_str = letter_map[exp]
        else:
            exp_as_aop_val = AoPValue.from_number(exp, base=current_base)
            formatted_exp = format_as_aop(exp_as_aop_val, letter_map)

            # Store the raw, un-parenthesized formatted exponent for analysis
            _sub_format_logs.append((exp, formatted_exp))

            if ' + ' in formatted_exp or ' - ' in formatted_exp:
                 formatted_exp = f"({formatted_exp})"

            exp_str = f"{base_symbol}^{formatted_exp}"

        parts.append(f"{coeff_str}{exp_str}")

    result = " + ".join(parts).replace(" + -", " - ")

    _format_depth -= 1

    if is_top_level_call:
        if _sub_format_logs:
            direct_mappings = []
            simple_polys = []
            nested_polys = []

            logged_exps = set()
            for exp, f_exp in _sub_format_logs:
                if exp in logged_exps: continue
                logged_exps.add(exp)

                log_line = f"exp {exp:<5} -> '{f_exp}'"
                if "a^" in f_exp:
                    nested_polys.append(log_line)
                elif " + " in f_exp or " - " in f_exp:
                    simple_polys.append(log_line)
                else:
                    direct_mappings.append(log_line)

            log_format_details(sorted(direct_mappings), "Direct Mappings")
            log_format_details(sorted(simple_polys), "Simple Polynomials")
            log_format_details(sorted(nested_polys), "Nested Exponents")

    return result


from .aop_logger import log_format_report_start, log_format_details, log_line

def format_as_decimal_string(val: AoPValue) -> str:
    """Translates the sparse polynomial into a full decimal string."""
    numerical_value = val.to_numerical()
    return str(numerical_value)
