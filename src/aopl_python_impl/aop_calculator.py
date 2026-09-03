# aopl_python_impl/aop_calculator.py
#
# This module contains the main AoP_Calculator class, which serves as the primary
# engine for the application. It manages state (like variables), handles caching,
# and orchestrates the tokenizing, parsing, and evaluation pipeline.
from __future__ import annotations
from typing import Tuple, Optional
from .definitions import AoPError
from .constants import EXPONENT_TO_LETTER_MAP
from .aop_parser import tokenize_expression, Parser, strip_digit_group_commas
from .aop_formatter import format_as_aop, format_as_decimal_string
from .aop_operations import evaluate_ast, _resolve_to_value
from .aop_value import AoPValue
import logging, os, json
from .aop_logger import print_legend, log_eval_report_start, DebugTimer, is_debug_timer_enabled
from .aop_ast import ASTNode
from .definitions import SymbolicPowerResult
from .aop_cache import (
    decode_aop_value,
    empty_cache,
    encode_aop_value,
    find_poly_entry,
    is_usable_cache,
    store_result,
)


class AoP_Calculator:
    def __init__(self, base: int = 10, cache_file: Optional[str] = None):
        self.base = base
        self.cache_file = cache_file
        self.cache = self._load_cache() if cache_file else None
        self.cache_dirty = False
        self.variables = {}

    def format_value(self, value: AoPValue, mode: str = "num") -> str:
        try:
            if mode == "aop":
                return format_as_aop(value, EXPONENT_TO_LETTER_MAP)
            return format_as_decimal_string(value)
        except (ValueError, OverflowError) as e:
            raise AoPError(str(e)) from e

    def _parse(self, expression: str) -> Optional[ASTNode]:
        tokens = tokenize_expression(expression)
        if not tokens:
            return None
        return Parser(tokens).parse()

    def evaluate(self, expression: str) -> Tuple[Optional[AoPValue], Optional[ASTNode]]:
        """Parse and evaluate. Returns (value, ast). Empty input is (None, None)."""
        expression = strip_digit_group_commas(expression)
        print_legend(expression, self.base)

        try:
            timer = DebugTimer(enabled=is_debug_timer_enabled())
            timer.lap("Cache Check")

            cached = find_poly_entry(self.cache, expression, self.base)
            if cached is not None:
                _key, entry = cached
                ast = self._parse(expression)
                try:
                    value = decode_aop_value(entry)
                except (KeyError, TypeError, ValueError):
                    value = None
                if value is not None:
                    timer.report()
                    return value, ast

            ast = self._parse(expression)
            timer.lap("Tokenize")
            timer.lap("Parse AST")
            if ast is None:
                return None, None
            log_eval_report_start(repr(ast))
            result_obj = evaluate_ast(ast, self.base, {}, self.variables)
            timer.lap("Evaluate AST")

            final_aop_value = _resolve_to_value(result_obj)
            timer.lap("Resolve Value")

            if isinstance(final_aop_value, SymbolicPowerResult):
                raise AoPError("Result is symbolic and cannot be represented.")

            if self.cache is not None:
                store_result(
                    self.cache,
                    expression,
                    None,
                    encode_aop_value(final_aop_value),
                    None,
                )
                self.cache_dirty = True

            timer.report()
            return final_aop_value, ast

        except AoPError:
            raise
        except (ValueError, SyntaxError, NameError, TypeError) as e:
            raise AoPError(str(e)) from e

    def evaluate_expression(self, expression: str, mode: str = "num") -> Tuple[str, Optional[ASTNode]]:
        """Evaluate and format. Prefer `evaluate` when the caller wants the value."""
        expression = strip_digit_group_commas(expression)
        cached = find_poly_entry(self.cache, expression, self.base)
        if cached is not None:
            _key, entry = cached
            if mode in entry:
                return entry[mode], self._parse(expression)

        value, ast = self.evaluate(expression)
        if value is None:
            return "", ast

        formatted = self.format_value(value, mode)
        if self.cache is not None:
            store_result(
                self.cache,
                expression,
                mode,
                encode_aop_value(value),
                formatted,
            )
            self.cache_dirty = True
        return formatted, ast

    def _load_cache(self):
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if is_usable_cache(data):
                    return data
                logging.warning("Ignoring incompatible or pickle-based calculator cache.")
            except Exception as e:
                logging.warning(f"Failed to load cache: {e}")
        return empty_cache()

    def save_cache(self):
        if not self.cache or not self.cache_dirty or not self.cache_file:
            return
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)
        self.cache_dirty = False
