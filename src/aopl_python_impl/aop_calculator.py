# aopl_python_impl/aop_calculator.py
from .definitions import TOKEN_REGEX, AoPError
from .aop_parser import tokenize_expression, Parser
from .aop_formatter import format_as_decimal_string
from .aop_operations import evaluate_ast
import logging

class AoP_Calculator:
    def __init__(self, base: int = 10):
        self.base = base
        self.token_regex = TOKEN_REGEX

    def evaluate_expression(self, expression: str) -> str:
        try:
            tokens = tokenize_expression(expression)
            if not tokens: return ""
            parser = Parser(tokens)
            ast = parser.parse()
            logging.debug(f"AST: {ast}")
            # The result is now an AoPValue object, which holds the polynomial representation.
            result_aop = evaluate_ast(ast, self.base)
            # We format it as a decimal string for the final output.
            return format_as_decimal_string(result_aop)
        except (AoPError, ValueError, TypeError, ZeroDivisionError) as e:
            return f"Error: {e}"
        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: An unexpected system error occurred."
