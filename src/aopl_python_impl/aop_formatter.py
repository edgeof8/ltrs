# aopl_python_impl/aop_formatter.py
from .aop_value import AoPValue

def format_as_aop(val: AoPValue, letter_map: dict) -> str:
    """Formats the polynomial into a symbolic letter string like 'd + 2c + b'."""
    if not val.poly: return "0"
    parts = []
    for exp, coeff in sorted(val.poly.items(), reverse=True):
        if coeff == 0: continue

        display_coeff = -coeff if val.is_negative else coeff
        coeff_str = ""
        if abs(display_coeff) != 1 or exp == 0: coeff_str = str(display_coeff)
        if display_coeff == -1 and exp != 0: coeff_str = "-"

        exp_str = letter_map.get(exp, f"base^{exp}") if exp != 0 else ""
        parts.append(f"{coeff_str}{exp_str}")

    result = " + ".join(parts).replace(" + -", " - ")
    return result

def format_as_decimal_string(val: AoPValue) -> str:
    """Translates the sparse polynomial into a full decimal string."""
    # This is the single source of truth for numerical conversion.
    # The previous implementation had a buggy re-implementation of carry logic.
    # This correctly handles all cases by relying on the core AoPValue method.
    numerical_value = val.to_numerical()
    return str(numerical_value)
