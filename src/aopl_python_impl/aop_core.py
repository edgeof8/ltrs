# aopl_python_impl/aop_core.py
#
# This module provides a simplified, functional, and stateless API for the calculator.
# It's designed for one-off calculations where maintaining state (like variables)
# across multiple calls is not required. For stateful sessions, users should
# instantiate and use the AoP_Calculator class directly.

from .aop_calculator import AoP_Calculator
from .definitions import AoPError

__all__ = ["evaluate_expression", "AoPError"]

# Create a single, module-level instance to be reused.
_shared_aop_calculator: AoP_Calculator = AoP_Calculator()

def evaluate_expression(expression_str: str) -> str:
    """
    Evaluates a complete Alphabet of Powers expression string using a shared,
    reset calculator instance. This function ensures stateless behavior for each call
    by clearing variables from the shared instance. For persistent variables
    across calls, create and use an AoP_Calculator instance directly.

    Args:
        expression_str: The AoP expression string to evaluate.

    Returns:
        A string representing the calculated AoP value.

    Raises:
        AoPError: If the expression cannot be evaluated.
    """
    # Clear any variables from previous calls to ensure stateless behavior for this API
    _shared_aop_calculator.variables.clear()

    # We only care about the result string here, not the AST.
    result_str, _ = _shared_aop_calculator.evaluate_expression(
        expression=expression_str, mode="num")
    return result_str

# Note: For any functions that might rely on or modify calculator state (like variables),
# it's generally better to require the user to instantiate and use AoP_Calculator directly.
# This simplified API in aop_core.py is for very basic, stateless operations.
