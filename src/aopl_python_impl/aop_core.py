# aopl_python_impl/aop_core.py
#
# This module provides a simplified, functional, and stateless API for the calculator.
# It's designed for one-off calculations where maintaining state (like variables)
# across multiple calls is not required. For stateful sessions, users should
# instantiate and use the AoP_Calculator class directly.

from .aop_calculator import AoP_Calculator
from .aop_value import AoPValue
from .definitions import AoPError

__all__ = ["evaluate", "evaluate_expression", "AoPError"]

# Create a single, module-level instance to be reused.
_shared_aop_calculator: AoP_Calculator = AoP_Calculator()

def evaluate(expression_str: str) -> AoPValue:
    """Evaluate an expression to an AoPValue, with no variables carried over."""
    _shared_aop_calculator.variables.clear()
    value, _ = _shared_aop_calculator.evaluate(expression_str)
    if value is None:
        raise AoPError("Empty expression.")
    return value


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
    value = evaluate(expression_str)
    return _shared_aop_calculator.format_value(value, "num")
