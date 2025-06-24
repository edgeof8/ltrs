# aop_core.py - Simplified functional interface
# This module provides a simple, function-based API that delegates
# to an instance of the AoP_Calculator class from aop_calculator.py.
# For more advanced usage or stateful calculations (like variables),
# import and use AoP_Calculator directly from aop_calculator.py.

from .aop_calculator import AoP_Calculator
# FIX: Removed unused imports for ValueTuple and a non-existent CalculatorInterface.
from .definitions import OutputFormatMode

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
        A string representing the calculated AoP value or an error message.
    """
    # Clear any variables from previous calls to ensure stateless behavior for this API
    _shared_aop_calculator.variables.clear()

    # FIX: The call to evaluate_expression was missing required arguments.
    # This now provides default values for mode and precision, making the
    # simple API functional again.
    return _shared_aop_calculator.evaluate_expression(
        expression=expression_str,
        mode=OutputFormatMode.AUTO,
        precision=10
    )

# evaluate_simple_word function was removed as it's redundant.
# evaluate_expression can handle simple words.

# Note: For any functions that might rely on or modify calculator state (like variables),
# it's generally better to require the user to instantiate and use AoP_Calculator directly.
# This simplified API in aop_core.py is for very basic, stateless operations.
