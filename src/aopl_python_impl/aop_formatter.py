# aopl_python_impl/aop_formatter.py
from .aop_value import AoPValue
from .aop_ast import ASTNode, SymbolicPowerNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode
from .definitions import SymbolicPowerResult, key_to_int, int_to_key, EXPONENT_TO_LETTER_MAP
import logging

_format_depth = 0
_sub_format_logs = []

def _format_number_in_base(n: int, base: int) -> str:
    if n == 0: return "0"
    if base < 2 or base > 36: raise ValueError("Base must be between 2 and 36")
    is_negative = n < 0
    if is_negative: n = -n
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = ""
    while n > 0:
        res = digits[n % base] + res
        n //= base
    return "-" + res if is_negative else res

def format_as_aop(val, letter_map: dict) -> str:
    if isinstance(val, SymbolicPowerResult):
        base_str = format_as_aop(val.base, letter_map)
        exp_str = format_as_aop(val.exponent, letter_map)
        if ' + ' in base_str or ' - ' in base_str: base_str = f"({base_str})"
        if ' + ' in exp_str or ' - ' in exp_str: exp_str = f"({exp_str})"
        return f"{base_str}^{exp_str}"
    elif isinstance(val, SymbolicPowerNode):
        return _format_symbolic_power(val, letter_map)
    elif isinstance(val, AoPValue):
        return _format_polynomial(val, letter_map)
    elif isinstance(val, ASTNode):
        return val.to_str()
    else:
        return str(val)

def _format_symbolic_power(val, letter_map: dict) -> str:
    if isinstance(val, SymbolicPowerNode):
        base_str = format_as_aop(val.base, letter_map)
        exp_str = format_as_aop(val.exponent, letter_map)
    else:
        return str(val)
    if ' + ' in base_str or ' - ' in base_str: base_str = f"({base_str})"
    if ' + ' in exp_str or ' - ' in exp_str: exp_str = f"({exp_str})"
    return f"{base_str}^{exp_str}"

def _format_polynomial(val: AoPValue, letter_map: dict) -> str:
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
    # Use 'a' as the symbolic representation of the current base in nested exponents
    base_symbol = int_to_key(1, current_base)
    parts = []

    sorted_poly = sorted(val.poly.items(), key=lambda item: int(item[0]), reverse=True)

    for exp_str, coeff in sorted_poly:
        if coeff == 0: continue

        exp_num = int(exp_str)
        display_coeff = -coeff if val.is_negative else coeff

        coeff_str = ""
        if abs(display_coeff) != 1 or exp_num == 0:
            coeff_str = str(display_coeff)
        elif display_coeff == -1:
            coeff_str = "-"

        # --- RECURSIVE FORMATTING LOGIC ---
        if exp_num == 0:
            exp_str_formatted = ""
        # If there's a direct letter mapping, use it.
        elif exp_num in EXPONENT_TO_LETTER_MAP:
            exp_str_formatted = EXPONENT_TO_LETTER_MAP[exp_num]
        # Otherwise, the exponent is complex and must be formatted recursively.
        else:
            # Create a new AoPValue just for the exponent's value.
            exp_as_aop_val = AoPValue.from_number(exp_num, base=current_base)
            # Recursively call this formatting function on the new AoPValue.
            formatted_exp = format_as_aop(exp_as_aop_val, letter_map)

            # Add to logs for debugging complex formats
            _sub_format_logs.append((exp_num, formatted_exp))

            # If the formatted exponent is complex, wrap it in parentheses.
            if ' + ' in formatted_exp or ' - ' in formatted_exp:
                formatted_exp = f"({formatted_exp})"

            # The final representation is base^(formatted_exponent)
            exp_str_formatted = f"{base_symbol}^({formatted_exp})"

        # Combine coefficient and exponent parts
        if exp_num == 0:
            parts.append(f"{coeff_str}")
        else:
            op = "*" if coeff_str and coeff_str != "-" else ""
            parts.append(f"{coeff_str}{op}{exp_str_formatted}")

    result = " + ".join(parts).replace(" + -", " - ")
    if result.startswith("+"):
        result = result[1:]

    _format_depth -= 1
    if is_top_level_call and _sub_format_logs:
        direct_mappings, simple_polys, nested_polys = [], [], []
        logged_exps = set()
        for exp_val, f_exp in _sub_format_logs:
            if exp_val in logged_exps: continue
            logged_exps.add(exp_val)
            log_line = f"exp {exp_val:<5} -> '{f_exp}'"
            if "a^" in f_exp: nested_polys.append(log_line)
            elif " + " in f_exp or " - " in f_exp: simple_polys.append(log_line)
            else: direct_mappings.append(log_line)
        log_format_details(sorted(direct_mappings), "Direct Mappings")
        log_format_details(sorted(simple_polys), "Simple Polynomials")
        log_format_details(sorted(nested_polys), "Nested Exponents")
    return result

from .aop_logger import log_format_report_start, log_format_details, log_line

def format_as_decimal_string(val: AoPValue) -> str:
    numerical_value = val.to_numerical()
    return str(numerical_value)
