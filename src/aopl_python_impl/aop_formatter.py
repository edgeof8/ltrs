# aopl_python_impl/aop_formatter.py
from .aop_value import AoPValue
from .definitions import SymbolicPowerResult
from .aop_ast import ASTNode

def format_as_aop(val, letter_map=None, resolver_func=None):
    if isinstance(val, SymbolicPowerResult):
        base_str = format_as_aop(val.base)
        exp_str = format_as_aop(val.exponent)
        if ' ' in base_str or '^' in base_str: base_str = f"({base_str})"
        if ' ' in exp_str or '^' in exp_str: exp_str = f"({exp_str})"
        return f"{base_str}^{exp_str}"
    elif isinstance(val, AoPValue):
        return _format_aopvalue_to_aop_string(val)
    elif isinstance(val, ASTNode):
        return val.to_str()
    return str(val)

def _format_aopvalue_to_aop_string(val: AoPValue) -> str:
    rust_obj = val._rust_obj
    coeff = rust_obj.coeff
    poly = rust_obj.get_poly()

    if coeff == 0: return "0"

    # Case 1: Pure power (coeff=1, single term with poly_coeff=1)
    if coeff == 1 and len(poly) == 1:
        exp_str, poly_coeff = list(poly.items())[0]
        if poly_coeff == 1:
            # This is the base^E case. We need to format E.
            # Create an AoPValue representing the exponent E.
            exponent_as_aop_val = AoPValue.from_number(int(exp_str), val._rust_obj.base)

            # Now, recursively format this new AoPValue.
            formatted_exponent = format_as_aop(exponent_as_aop_val)

            # If the formatted exponent is a simple number or single letter, we're good.
            # If it's a complex expression, wrap it in parentheses.
            if ' ' in formatted_exponent or '+' in formatted_exponent or '*' in formatted_exponent:
                 return f"a^({formatted_exponent})"
            else:
                 return f"a^{formatted_exponent}"

    # Fallback for all other cases (numbers, complex polynomials)
    if not poly:
        return str(coeff)

    # Case 4: Full polynomial representation
    # Sort terms by exponent descending for canonical output
    sorted_terms = sorted(poly.items(), key=lambda item: int(item[0]), reverse=True)
    parts = []
    for i, (exp_str, poly_coeff_val) in enumerate(sorted_terms):
        sign_str = " + " if poly_coeff_val > 0 else " - "
        if i == 0 and poly_coeff_val > 0: sign_str = ""
        if i == 0 and poly_coeff_val < 0: sign_str = "-"
        coeff_abs = abs(poly_coeff_val)
        term_coeff_str = f"{coeff_abs}*" if coeff_abs != 1 else ""
        exp_part = AoPValue.int_to_key(exp_str) if exp_str != "0" else ""
        if exp_str == "0":
            term_str = f"{sign_str}{coeff_abs}"
        else:
            term_str = f"{sign_str}{term_coeff_str}{exp_part}"
        parts.append(term_str)
    poly_str = "".join(parts).lstrip()
    if coeff == 1: return poly_str
    if coeff == -1: return f"-({poly_str})"
    return f"{coeff} * ({poly_str})"

def format_as_decimal_string(val: AoPValue) -> str:
    return str(val.to_numerical())
