# aopl_python_impl/aop_calculator.py

import re
from .definitions import (
    OutputFormatMode, OPERATORS, TOKEN_REGEX,
    LETTER_TO_EXPONENT_MAP, EXPONENT_TO_LETTER_MAP, AoPError
)
from .aop_value import AoPValue
from .aop_parser import tokenize_expression, infix_to_rpn, evaluate_rpn
from .aop_term_handler import get_term_value
from .aop_formatter import format_output
from .aop_operations import simplify_value

class AoP_Calculator:
    def __init__(self, base: int = 10): # Removed aop_letters parameter
        self.base = base
        # Use the comprehensive maps directly from definitions
        self.letter_to_exponent = LETTER_TO_EXPONENT_MAP
        self.exponent_to_letter = EXPONENT_TO_LETTER_MAP

        self.token_regex = TOKEN_REGEX

        self.variables: dict[str, AoPValue] = {}
        self.output_format_mode = OutputFormatMode.AUTO
        self.precision = 10
        self.operators_map = OPERATORS.copy()

    def set_power_associativity(self, mode: str):
        if mode.lower() == 'right':
            self.operators_map['^']['associativity'] = 'right'
            self.operators_map['**']['associativity'] = 'right'
        elif mode.lower() == 'left':
            self.operators_map['^']['associativity'] = 'left'
            self.operators_map['**']['associativity'] = 'left'
        else:
            raise ValueError("Invalid associativity mode. Use 'left' or 'right'.")

    def evaluate_expression(self, expression: str) -> str:
        try:
            tokens = tokenize_expression(expression, self.token_regex)
            rpn = infix_to_rpn(tokens, self.operators_map)
            result = evaluate_rpn(rpn, self.variables, get_term_value, self.base)

            def get_letter_func(exp: int) -> str:
                return self.exponent_to_letter.get(exp, "")

            return format_output(
                result, self.base, get_letter_func, self.output_format_mode, self.precision
            )
        except (AoPError, ZeroDivisionError, OverflowError, ValueError, NotImplementedError) as e:
            # Return the raw string of the exception for now, to simplify debugging.
            return str(e)
