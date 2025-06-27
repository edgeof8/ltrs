# aopl_python_impl/aop_calculator.py
from .definitions import TOKEN_REGEX, AoPError, EXPONENT_TO_LETTER_MAP
from .aop_parser import tokenize_expression, Parser
# --- MODIFIED ---: Import both formatters
from .aop_formatter import format_as_decimal_string, format_as_aop
from .aop_operations import evaluate_ast
import logging

class AoP_Calculator:
    def __init__(self, base: int = 10):
        self.base = base
        self.token_regex = TOKEN_REGEX

    # --- MODIFIED ---: Accept 'mode' argument to control output format
    def evaluate_expression(self, expression: str, mode: str = "num") -> str:
        try:
            tokens = tokenize_expression(expression)
            if not tokens: return ""
            parser = Parser(tokens)
            ast = parser.parse()
            logging.debug(f"AST: {ast}")

            result_aop = evaluate_ast(ast, self.base)

            # --- NEW ---: Choose formatter based on the selected mode
            if mode == "aop":
                # Use the symbolic letter-based formatter
                return format_as_aop(result_aop, EXPONENT_TO_LETTER_MAP)
            else: # "num" is the default
                # Use the standard decimal string formatter
                return format_as_decimal_string(result_aop)

        except (AoPError, ValueError, TypeError, ZeroDivisionError) as e:
            return f"Error: {e}"
        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: An unexpected system error occurred."
