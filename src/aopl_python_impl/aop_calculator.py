# aopl_python_impl/aop_calculator.py
#
# This module contains the main AoP_Calculator class, which serves as the primary
# engine for the application. It manages state (like variables), handles caching,
# and orchestrates the tokenizing, parsing, and evaluation pipeline.
from __future__ import annotations
from typing import Tuple, Optional
from .definitions import AoPError
from .constants import EXPONENT_TO_LETTER_MAP
from .aop_parser import tokenize_expression, Parser
from .aop_formatter import format_as_aop, format_as_decimal_string
from .aop_operations import evaluate_ast, _resolve_to_value
import logging, os, json, pickle, base64
from .aop_logger import print_legend, log_eval_report_start, DebugTimer
from .aop_value import AoPValue
from .aop_ast import ASTNode
from .definitions import SymbolicPowerResult

CACHE_FILENAME = 'precalculated_cache_v2.json'

class AoP_Calculator:
    def __init__(self, base: int = 10):
        self.base = base
        self.cache = self._load_cache()
        self.cache_dirty = False
        self.variables = {}

    def evaluate_expression(self, expression: str, mode: str = "num") -> Tuple[str, Optional[ASTNode]]:
        # The logger functions will only print if the global flag is set
        print_legend(expression, self.base)

        try:
            timer = DebugTimer(enabled=True)
            timer.lap("Cache Check")
            base_str = str(self.base)

            if self.cache and base_str in self.cache and expression in self.cache[base_str]:
                cached_data = self.cache[base_str][expression]
                if "raw_pickle" in cached_data:
                    # On a full cache hit for the requested mode, return the cached result.
                    # We will re-parse to get the AST for the explainer if needed.
                    if mode in cached_data:
                        cached_result = cached_data[mode]
                        # Re-parsing is cheap compared to re-evaluating. We do it here
                        # to ensure the AI explainer always has an AST to work with,
                        # even when the calculation result comes from the cache.
                        tokens = tokenize_expression(expression)
                        parser = Parser(tokens)
                        ast = parser.parse() # We need the AST for the explainer.
                        timer.report()
                        return cached_result, ast
            else:
                result_obj = None

            if result_obj is None:
                tokens = tokenize_expression(expression)
                timer.lap("Tokenize")
                if not tokens: return "", None
                parser = Parser(tokens)
                ast = parser.parse()
                timer.lap("Parse AST")
                if ast is None: return "", None # Handle empty expressions
                log_eval_report_start(repr(ast))
                # Pass the cache object down to the AST evaluator
                result_obj = evaluate_ast(ast, self.base, self.cache, self.variables)
                timer.lap("Evaluate AST")

            # --- ALWAYS resolve the result to a final AoPValue ---
            final_aop_value = _resolve_to_value(result_obj)
            timer.lap("Resolve Value")

            if isinstance(final_aop_value, SymbolicPowerResult):
                return "Error: Result is symbolic and cannot be represented.", None

            if mode == "aop":
                final_result_str = format_as_aop(final_aop_value, EXPONENT_TO_LETTER_MAP)
                cacheable_obj = final_aop_value
                timer.lap("Format Output")
            else: # "num" mode
                final_result_str = format_as_decimal_string(final_aop_value)
                cacheable_obj = final_aop_value
                timer.lap("Format Output")

            if self.cache is not None:
                pickled_obj = pickle.dumps(cacheable_obj)
                b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
                if base_str not in self.cache: self.cache[base_str] = {}
                if expression not in self.cache[base_str]: self.cache[base_str][expression] = {}
                self.cache[base_str][expression]["raw_pickle"] = b64_pickle
                self.cache[base_str][expression][mode] = final_result_str
                self.cache_dirty = True

            timer.report()
            return final_result_str, ast

        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: {type(e).__name__}: {e}", None

    def _load_cache(self):
        cache_file = os.path.join('research', 'experiment_results', 'cache', CACHE_FILENAME)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f: return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cache: {e}")
                return {} # Return empty dict on failure
        return {} # Return empty dict if file doesn't exist

    def save_cache(self):
        if not self.cache or not self.cache_dirty:
            return

        cache_dir = os.path.join('research', 'experiment_results', 'cache')
