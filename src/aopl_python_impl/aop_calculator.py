# aopl_python_impl/aop_calculator.py

from .aop_parser import tokenize_expression, infix_to_rpn, evaluate_rpn, OPERATORS
from .aop_term_handler import get_term_value
from .aop_formatter import format_output
from .definitions import OutputFormatMode, ValueTuple, AoPError
from typing import Dict, Callable

class AoPCalculator:
    def __init__(self, base: int = 10, output_mode: OutputFormatMode = OutputFormatMode.AUTO, precision: int = 10):
        self.base = base
        self.output_mode = output_mode
        self.precision = precision
        self.variables: Dict[str, ValueTuple] = {}

    def get_letter(self, exponent: int) -> str:
        from .definitions import EXPONENT_TO_LETTER_MAP
        return EXPONENT_TO_LETTER_MAP.get(exponent, "")

    def represent_exponent(self, exponent: int, base: int, get_letter_func: Callable[[int], str]) -> str:
        from .aop_formatter import represent_exponent_as_aop_term
        return represent_exponent_as_aop_term(exponent, base, get_letter_func)

    def normalize(self, value: ValueTuple) -> ValueTuple:
        from .aop_operations import simplify_value
        return simplify_value(value, self.base)

    def evaluate(self, expression: str) -> ValueTuple:
        try:
            from .definitions import TOKEN_REGEX
            tokens = tokenize_expression(expression, TOKEN_REGEX)
            rpn_tokens = infix_to_rpn(tokens, OPERATORS)
            result = evaluate_rpn(rpn_tokens, self.variables, get_term_value, self.base)
            return self.normalize(result)
        except AoPError as e:
            raise ValueError(f"Error in expression '{expression}': {e.message}") from e
        except Exception as e:
            raise ValueError(f"Unexpected error: {str(e)}") from e

    def calculate(self, expression: str) -> str:
        result = self.evaluate(expression)
        return format_output(result, self.base, self.get_letter, self.represent_exponent, self.output_mode, self.normalize, self.precision)
