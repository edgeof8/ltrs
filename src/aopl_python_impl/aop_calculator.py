# aopl_python_impl/aop_calculator.py
from .definitions import TOKEN_REGEX, AoPError, EXPONENT_TO_LETTER_MAP, SymbolicPowerResult
from .aop_parser import tokenize_expression, Parser
from .aop_formatter import format_as_aop, format_as_decimal_string
from .aop_operations import evaluate_ast, _resolve_to_value
import logging, os, json, pickle, base64
from .aop_logger import print_legend, log_eval_report_start, DebugTimer, log_pow
from .aop_value import AoPValue

CACHE_FILENAME = 'precalculated_cache_v2.json'

# --- FIX: Ensure the class name is AoP_Calculator ---
class AoP_Calculator:
    def __init__(self, base: int = 10):
        self.base = base
        self.cache = self._load_cache()
        self.cache_dirty = False

    def evaluate_expression(self, expression: str, mode: str = "num") -> str:
        try:
            timer = None
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                timer = DebugTimer()

            print_legend(expression, self.base)
            base_str = str(self.base)
            result_obj = None

            if timer: timer.lap("Cache Check")

            if self.cache and base_str in self.cache and expression in self.cache[base_str]:
                cached_data = self.cache[base_str][expression]
                if "raw_pickle" in cached_data:
                    result_obj = pickle.loads(base64.b64decode(cached_data["raw_pickle"]))
                    if mode in cached_data:
                        return cached_data[mode]

            if result_obj is None:
                logging.debug(f"Cache miss for '{expression}' (base {base_str}). Computing from scratch.")
                tokens = tokenize_expression(expression)
                if timer: timer.lap("Tokenize")
                if not tokens: return ""
                parser = Parser(tokens)
                ast = parser.parse()
                if timer: timer.lap("Parse AST")
                if ast is None: return "" # Handle empty expressions
                log_eval_report_start(repr(ast))
                result_obj = evaluate_ast(ast, self.base, self.cache)
                if timer: timer.lap("Evaluate AST")

            if mode == "aop":
                final_result_str = format_as_aop(result_obj, EXPONENT_TO_LETTER_MAP, _resolve_to_value)
                cacheable_obj = result_obj
                if timer: timer.lap("Format Output")
            else: # "num" mode
                final_aop_value = _resolve_to_value(result_obj)
                if timer: timer.lap("Resolve Value")
                if isinstance(final_aop_value, SymbolicPowerResult):
                    return "Error: Result is symbolic and cannot be represented numerically."
                final_result_str = format_as_decimal_string(final_aop_value)
                cacheable_obj = final_aop_value
                if timer: timer.lap("Format Output")

            if self.cache is not None:
                pickled_obj = pickle.dumps(cacheable_obj)
                b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
                if base_str not in self.cache: self.cache[base_str] = {}
                if expression not in self.cache[base_str]: self.cache[base_str][expression] = {}
                self.cache[base_str][expression]["raw_pickle"] = b64_pickle
                self.cache[base_str][expression][mode] = final_result_str
                self.cache_dirty = True

            if timer: timer.report()
            return final_result_str

        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: {type(e).__name__}: {e}"

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
