# aopl_python_impl/aop_formatter.py
from .aop_value import AoPValue
from .definitions import SymbolicPowerResult, EXPONENT_TO_LETTER_MAP
from .aop_ast import ASTNode

def format_as_aop(val, letter_map=None, resolver_func=None):
    if letter_map is None:
        letter_map = EXPONENT_TO_LETTER_MAP

    if isinstance(val, SymbolicPowerResult):
        base_str = format_as_aop(val.base, letter_map, resolver_func)
        exp_str = format_as_aop(val.exponent, letter_map, resolver_func)
        if ' ' in base_str: base_str = f"({base_str})"
        if ' ' in exp_str: exp_str = f"({exp_str})"
        return f"{base_str}^{exp_str}"
    elif isinstance(val, AoPValue):
        # Use the Rust object's __repr__ which is now the source of truth
        return val._rust_obj.__repr__()
    elif isinstance(val, ASTNode):
        return val.to_str()
    return str(val)

# This function is no longer needed as the Rust __repr__ is better.
# We keep it here to avoid breaking other code that might call it, but it's deprecated.
def _format_polynomial(val: AoPValue) -> str:
    return val._rust_obj.__repr__()

def format_as_decimal_string(val: AoPValue) -> str:
    return str(val.to_numerical())
