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
            # Check for precalculated result in cache before computing
            cache = self._load_cache()
            if cache and str(self.base) in cache and expression in cache[str(self.base)]:
                result_aop = cache[str(self.base)][expression]
                if isinstance(result_aop, str) and result_aop.startswith("Error"):
                    return result_aop
                # Since cached results are strings, we return them as-is or format if needed
                # For now, assuming the cache stores formatted AOP or numeric strings directly
                return result_aop

            # If not in cache, compute as usual
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
            else:  # "num" is the default
                # Use the standard decimal string formatter
                return format_as_decimal_string(result_aop)

        except (AoPError, ValueError, TypeError, ZeroDivisionError) as e:
            return f"Error: {e}"
        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: An unexpected system error occurred."

    def _load_cache(self):
        """Load the precalculated cache from file if available."""
        import os
        import json
        cache_file = os.path.join('research', 'experiment_results', 'cache', 'precalculated_values.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cache: {e}")
                return None
        return None
