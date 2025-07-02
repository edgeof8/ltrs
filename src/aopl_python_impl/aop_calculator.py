# aopl_python_impl/aop_calculator.py
from .definitions import TOKEN_REGEX, AoPError, EXPONENT_TO_LETTER_MAP, SymbolicPowerResult
from .aop_parser import tokenize_expression, Parser
from .aop_formatter import format_as_aop, format_as_decimal_string
from .aop_operations import evaluate_ast
import logging, os, json, pickle, base64
from .aop_logger import print_legend, log_eval_report_start, log_pow
from .aop_value import AoPValue

CACHE_FILENAME = 'precalculated_cache_v2.json'

class AoP_Calculator:
    def __init__(self, base: int = 10):
        self.base = base
        self.cache = self._load_cache()
        self.cache_dirty = False

    def evaluate_expression(self, expression: str, mode: str = "num") -> str:
        try:
            print_legend(expression, self.base)
            base_str = str(self.base)
            result_obj = None

            if self.cache and base_str in self.cache and expression in self.cache[base_str]:
                cached_data = self.cache[base_str][expression]
                if "raw_pickle" in cached_data:
                    result_obj = pickle.loads(base64.b64decode(cached_data["raw_pickle"]))
                    if mode in cached_data:
                        return cached_data[mode]

            if result_obj is None:
                logging.debug(f"Cache miss for '{expression}' (base {base_str}). Computing from scratch.")
                tokens = tokenize_expression(expression)
                if not tokens: return ""
                parser = Parser(tokens)
                ast = parser.parse()
                log_eval_report_start(repr(ast))
                result_obj = evaluate_ast(ast, self.base, self.cache)

            # --- LAZY EVALUATION LOGIC ---
            if mode == "aop":
                # For 'aop' mode, we format the potentially symbolic object.
                # The formatter will intelligently resolve what it can.
                final_result_str = format_as_aop(result_obj, EXPONENT_TO_LETTER_MAP, self._resolve_to_value)
                cacheable_obj = result_obj
            else: # "num" mode requires full resolution
                final_aop_value = self._resolve_to_value(result_obj)
                if isinstance(final_aop_value, SymbolicPowerResult):
                    return "Error: Result is symbolic and cannot be represented numerically."
                final_result_str = format_as_decimal_string(final_aop_value)
                cacheable_obj = final_aop_value

            # Caching logic
            if self.cache is not None:
                pickled_obj = pickle.dumps(cacheable_obj)
                b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
                if base_str not in self.cache: self.cache[base_str] = {}
                if expression not in self.cache[base_str]: self.cache[base_str][expression] = {}
                self.cache[base_str][expression]["raw_pickle"] = b64_pickle
                self.cache[base_str][expression][mode] = final_result_str
                self.cache_dirty = True
            return final_result_str

        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: {type(e).__name__}: {e}"

    def _resolve_to_value(self, obj):
        """
        The authoritative, recursive resolver.
        Turns a potentially symbolic object into a single AoPValue.
        """
        current = obj
        # This loop flattens nested SymbolicPowerResult objects, e.g. (b^a)^t
        while isinstance(current, SymbolicPowerResult):
            log_pow(f"Resolving SymbolicPower: {current!r}")
            base = self._resolve_to_value(current.base)
            exponent = self._resolve_to_value(current.exponent)

            if isinstance(base, SymbolicPowerResult) or isinstance(exponent, SymbolicPowerResult):
                 return SymbolicPowerResult(base, exponent)

            try:
                current = base ** exponent
            except Exception as e:
                if type(e).__name__ == 'PyNotImplementedError':
                    log_pow(f"Power op is unresolvable. Returning symbolic: {current!r}")
                    return current
                raise e

        return current

    def _load_cache(self):
        cache_file = os.path.join('research', 'experiment_results', 'cache', CACHE_FILENAME)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def save_cache(self):
        if not self.cache or not self.cache_dirty: return
        cache_dir = os.path.join('research', 'experiment_results', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, CACHE_FILENAME)
        try:
            with open(cache_file, 'w') as f: json.dump(self.cache, f, indent=2)
            self.cache_dirty = False
        except Exception as e: logging.error(f"Failed to save cache: {e}")
