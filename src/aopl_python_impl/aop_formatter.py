# aopl_python_impl/aop_formatter.py
from .aop_value import AoPValue
from .definitions import SymbolicPowerResult, EXPONENT_TO_LETTER_MAP, int_to_key
from .aop_ast import ASTNode
import logging

def format_as_aop(val, letter_map, resolver_func=None):
    """Formats an AoP object into a string, with an optional resolver for symbolic powers."""
    if isinstance(val, SymbolicPowerResult):
        if resolver_func:
            resolved_val = resolver_func(val)
            if isinstance(resolved_val, AoPValue):
                return _format_polynomial(resolved_val, letter_map)

        # Pass the resolver function down in recursive calls
        base_str = format_as_aop(val.base, letter_map, resolver_func)
        exp_str = format_as_aop(val.exponent, letter_map, resolver_func)

        if ' + ' in base_str or ' - ' in base_str: base_str = f"({base_str})"
        if ' + ' in exp_str or ' - ' in exp_str: exp_str = f"({exp_str})"
        return f"{base_str}^{exp_str}"

    elif isinstance(val, AoPValue):
        return _format_polynomial(val, letter_map)
    elif isinstance(val, ASTNode):
        return val.to_str()
    return str(val)

def _format_polynomial(val: AoPValue, letter_map: dict) -> str:
    if not val.poly: return "0"
    parts = []
    sorted_poly = sorted(val.poly.items(), key=lambda item: int(item[0]), reverse=True)
    for exp_str, coeff in sorted_poly:
        exp_num = int(exp_str)
        display_coeff = -coeff if val.is_negative else coeff

        coeff_part = ""
        if abs(display_coeff) != 1 or exp_num == 0:
            coeff_part = str(display_coeff)
        elif display_coeff == -1:
            coeff_part = "-"

        exp_part = int_to_key(exp_num, val.base) if exp_num != 0 else ""

        if exp_part:
            op = "*" if coeff_part and coeff_part != "-" else ""
            parts.append(f"{coeff_part}{op}{exp_part}")
        else:
            parts.append(coeff_part)

    result = " + ".join(parts).replace(" + -", " - ")
    if result.startswith("+"): result = result[1:]
    return result if result else "0"

def format_as_decimal_string(val: AoPValue) -> str:
    return str(val.to_numerical())
