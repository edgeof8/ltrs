# aopl_python_impl/aop_calculator.py
import re
from .definitions import OutputFormatMode, OPERATORS, TOKEN_REGEX, AoPError, LETTER_TO_EXPONENT_MAP, EXPONENT_TO_LETTER_MAP
from .aop_value import AoPValue
from .aop_parser import tokenize_expression, infix_to_rpn, evaluate_rpn
from .aop_operations import simplify_value
from .aop_term_handler import get_term_value
from .aop_formatter import format_output

class AoP_Calculator:
    def __init__(self, base: int = 10, output_format_mode: OutputFormatMode = OutputFormatMode.AUTO, precision: int = 10):
        self.base = base
        self.output_format_mode = output_format_mode
        self.precision = precision
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

    def evaluate_expression(self, expression: str) -> str:
        try:
            tokens = tokenize_expression(expression, self.token_regex)
            rpn = infix_to_rpn(tokens, self.operators_map)
            result = evaluate_rpn(rpn, self.variables, get_term_value, self.base)
            simplified_result = simplify_value(result, self.base)
            def get_letter_func(exp: int) -> str:
                return self.exponent_to_letter.get(exp, "")
            return format_output(simplified_result, self.base, get_letter_func, self.output_format_mode, self.precision)
        except (AoPError, ZeroDivisionError, OverflowError, ValueError, NotImplementedError) as e:
            return str(e)
