# aopl_python_impl/aop_calculator.py
import re
import logging
from .definitions import OutputFormatMode, OPERATORS, TOKEN_REGEX, AoPError, LETTER_TO_EXPONENT_MAP, EXPONENT_TO_LETTER_MAP
from .aop_value import AoPValue
from .aop_parser import tokenize_expression, infix_to_rpn, evaluate_rpn
from .aop_operations import simplify_value
from .aop_term_handler import get_term_value
# --- THIS IS THE FIX ---
# Import the new master formatter function
from .aop_formatter import format_output
# --- END OF FIX ---

class AoP_Calculator:
    def __init__(self, base: int = 10):
        """Initializes the calculator with a specific base."""
        self.base = base
        self.letter_to_exponent = LETTER_TO_EXPONENT_MAP
        self.exponent_to_letter = EXPONENT_TO_LETTER_MAP
        self.token_regex = TOKEN_REGEX
        self.variables: dict[str, AoPValue] = {}
        self.operators_map = OPERATORS.copy()

    def set_power_associativity(self, mode: str):
        if mode.lower() in ('right', 'left'):
            self.operators_map['^']['associativity'] = mode.lower()
            self.operators_map['**']['associativity'] = mode.lower()
        else: raise ValueError("Invalid associativity mode. Use 'left' or 'right'.")

    def evaluate_expression(self, expression: str, mode: OutputFormatMode, precision: int) -> str:
        """
        Evaluates an expression and formats it according to the given mode and precision.
        """
        logging.debug(f"--- Starting Evaluation ---")
        logging.debug(f"Expression: '{expression}', Base: {self.base}, Mode: {mode.value}")
        try:
            tokens = tokenize_expression(expression, self.token_regex)
            rpn = infix_to_rpn(tokens, self.operators_map)
            result = evaluate_rpn(rpn, self.variables, get_term_value, self.base)
            logging.debug(f"Raw evaluation result: {result!r}")
            simplified_result = simplify_value(result, self.base)

            def get_letter_func(exp: int) -> str:
                return self.exponent_to_letter.get(exp, "")

            # --- THIS IS THE FIX ---
            # Call the new master formatter function instead of the old method
            logging.debug(f"Simplified result for formatting: {simplified_result!r}")
            return format_output(simplified_result, self.base, get_letter_func, mode, precision)
            # --- END OF FIX ---

        except (AoPError, ZeroDivisionError, OverflowError, ValueError, NotImplementedError) as e:
            logging.error(f"Evaluation error: {type(e).__name__}: {e}", exc_info=True)
            # Return a clean error string
            return f"Error: {e}"
