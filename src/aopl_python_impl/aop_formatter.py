# aopl_python_impl/aop_formatter.py
from .aop_value import AoPValue, int_to_key, key_to_int
from .aop_symbolic_power import SymbolicPower
from .aop_ast import ASTNode, SymbolicPowerNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode
from .aop_types import SymbolicPowerResult
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

# --- MODIFIED: This is now the main dispatcher ---
def format_as_aop(val, letter_map: dict) -> str:
    """Formats an AoP object (AoPValue, SymbolicPowerResult, etc.) into a string."""
    if isinstance(val, SymbolicPowerResult):
        base_str = format_as_aop(val.base, letter_map)
        exp_str = format_as_aop(val.exponent, letter_map)
        if ' + ' in base_str or ' - ' in base_str:
            base_str = f"({base_str})"
        if ' + ' in exp_str or ' - ' in exp_str:
            exp_str = f"({exp_str})"
        return f"{base_str}^{exp_str}"
    elif isinstance(val, SymbolicPowerNode):
        return _format_symbolic_power(val, letter_map)
    elif isinstance(val, SymbolicPower):
        return _format_symbolic_power(val, letter_map)
    elif isinstance(val, AoPValue):
        return _format_polynomial(val, letter_map)
    elif isinstance(val, ASTNode):  # Fallback for other AST nodes if they slip through
        return val.to_str()
    else:
        return str(val)  # Should not happen, but for safety

def _format_symbolic_power(val, letter_map: dict) -> str:
    """Formats a SymbolicPower or SymbolicPowerNode object like base^exponent."""
    if isinstance(val, SymbolicPower):
        base_str = format_as_aop(val.base, letter_map)
        exp_str = format_as_aop(val.exponent, letter_map)
    elif isinstance(val, SymbolicPowerNode):
        base_str = format_as_aop(val.base, letter_map)
        exp_str = format_as_aop(val.exponent, letter_map)
    else:
        return str(val)

    # Add parentheses if the base or exponent are complex expressions
    if ' + ' in base_str or ' - ' in base_str:
        base_str = f"({base_str})"
    if ' + ' in exp_str or ' - ' in exp_str:
        exp_str = f"({exp_str})"

    return f"{base_str}^{exp_str}"

def _format_polynomial(val: AoPValue, letter_map: dict) -> str:
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

        # Convert the string key from the dictionary into its integer value for lookups
        exp_num = key_to_int(exp, current_base) if isinstance(exp, str) else exp
        if exp_num == 0:
            exp_str = "" # This is a constant term
        elif exp_num in letter_map:
            # Correctly use the integer exponent to look up the letter
            exp_str = letter_map[exp_num]
        else:
            # This block is for exponents that are too large to be a single letter
            # e.g., for an exponent of 10100, we format it as "d + b"
            exp_as_aop_val = AoPValue.from_number(exp_num, base=current_base)
            formatted_exp = format_as_aop(exp_as_aop_val, letter_map)

            # Store the raw, un-parenthesized formatted exponent for analysis
            _sub_format_logs.append((exp_num, formatted_exp))

            if ' + ' in formatted_exp or ' - ' in formatted_exp:
                formatted_exp = f"({formatted_exp})"

            exp_str = f"{base_symbol}^{formatted_exp}"

        parts.append(f"{coeff_str}{exp_str}" if exp_num != 0 else f"{coeff_str}")

    result = " + ".join(parts).replace(" + -", " - ")

    _format_depth -= 1

    if is_top_level_call:
        if _sub_format_logs:
            direct_mappings = []
            simple_polys = []
            nested_polys = []

            logged_exps = set()
            for exp_val, f_exp in _sub_format_logs:
                if exp_val in logged_exps: continue
                logged_exps.add(exp_val)

                log_line = f"exp {exp_val:<5} -> '{f_exp}'"
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
