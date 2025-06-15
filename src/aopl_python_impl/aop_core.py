# aop_core.py - Simplified functional interface
# This module provides a simple, function-based API that delegates
# to an instance of the AoP_Calculator class from aop_calculator.py.
# For more advanced usage or stateful calculations (like variables),
# import and use AoP_Calculator directly from aop_calculator.py.

from .aop_calculator import AoP_Calculator
from .definitions import ValueTuple # Often useful for type hinting if users interact with raw values
from .interfaces import CalculatorInterface # Import the protocol

# Create a single, module-level instance to be reused.
# Type hint it with the protocol for better type safety and clarity.
_shared_aop_calculator: CalculatorInterface = AoP_Calculator()

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
    return _shared_aop_calculator.evaluate_expression(expression_str)

# evaluate_simple_word function was removed as it's redundant.
# evaluate_expression can handle simple words.

# Add other simple pass-through functions if desired, for example:
# def get_term_value_simple(term: str) -> ValueTuple:
#     # Ensure statelessness if using the shared calculator
#     _shared_aop_calculator.variables.clear()
#     # Note: get_term_value in AoP_Calculator might not exist anymore or its signature changed.
#     # This example assumes it would be adapted or AoP_Calculator would provide a suitable method.
#     # For now, direct use of aop_term_handler.get_term_value with an empty var dict is better for statelessness.
#     from .aop_term_handler import get_term_value
#     return get_term_value(term, {})


# Note: For any functions that might rely on or modify calculator state (like variables),
# it's generally better to require the user to instantiate and use AoP_Calculator directly.
# This simplified API in aop_core.py is for very basic, stateless operations.
