# aopl_python_impl/aop_calculator.py
from .definitions import TOKEN_REGEX, AoPError, EXPONENT_TO_LETTER_MAP
from .aop_parser import tokenize_expression, Parser
from .aop_formatter import format_as_aop, format_as_decimal_string
from .aop_operations import evaluate_ast
from .aop_types import SymbolicPowerResult
import logging
import os
import json
# --- NEW: Imports for pickling and encoding ---
import pickle
import base64
from .aop_logger import print_legend, log_eval_report_start, log_pow
from .aop_value import AoPValue, int_to_key # Import AoPValue for type hints and unpickling

# --- NEW: Define a new cache filename to avoid conflicts with the old format ---
CACHE_FILENAME = 'precalculated_cache_v2.json'

class AoP_Calculator:
    def __init__(self, base: int = 10):
        self.base = base
        self.token_regex = TOKEN_REGEX
        self.cache = self._load_cache()
        # --- NEW: Track if the cache has been modified ---
        self.cache_dirty = False

    def evaluate_expression(self, expression: str, mode: str = "num") -> str:
        try:
            print_legend(expression, self.base)
            base_str = str(self.base)

            # --- MODIFIED: New, efficient cache check ---
            if self.cache and base_str in self.cache and expression in self.cache[base_str]:
                cached_data = self.cache[base_str][expression]
                logging.debug(f"Cache hit for '{expression}' (base {base_str}). Cached data: {list(cached_data.keys())}")

                # 1. Fast path: If the requested format is already cached, return it directly.
                if mode in cached_data:
                    logging.debug(f"Returning pre-formatted '{mode}' from cache.")
                    return cached_data[mode]

                # 2. Slower path: If we have the raw object, use it to generate the requested format.
                if "raw_pickle" in cached_data:
                    logging.debug("Unpickling AoPValue from cache to generate new format.")
                    pickle_data = base64.b64decode(cached_data["raw_pickle"])
                    result_aop = pickle.loads(pickle_data)

                    # Format the unpickled object into the desired mode
                    if mode == "aop":
                        formatted_result = format_as_aop(result_aop, EXPONENT_TO_LETTER_MAP)
                    else: # "num"
                        formatted_result = format_as_decimal_string(result_aop)

                    # IMPORTANT: Update the cache with the newly generated format and save it.
                    self.cache[base_str][expression][mode] = formatted_result
                    self.cache_dirty = True
                    return formatted_result

            # --- If not in cache or cache is incomplete, compute as usual ---
            logging.debug(f"Cache miss for '{expression}' (base {base_str}). Computing from scratch.")
            tokens = tokenize_expression(expression)
            if not tokens: return ""
            parser = Parser(tokens)
            ast = parser.parse()

            log_eval_report_start(repr(ast))
            result_obj = evaluate_ast(ast, self.base, self.cache)

            # Format the result
            if mode == "aop":
                # The formatter now understands SymbolicPowerResult directly
                final_result_str = format_as_aop(result_obj, EXPONENT_TO_LETTER_MAP)
                # The object we want to cache is the unevaluated symbolic object
                cacheable_obj = result_obj
            else:  # "num" is the default
                # If the result is a symbolic power, we must evaluate it now
                if isinstance(result_obj, SymbolicPowerResult):
                    from .aop_operations import _exponentiate_aop_value
                    final_aop_value = _exponentiate_aop_value(result_obj.base, result_obj.exponent)
                else: # It was already a simple value
                    final_aop_value = result_obj

                final_result_str = format_as_decimal_string(final_aop_value)
                cacheable_obj = final_aop_value

            # --- MODIFIED: New cache update logic ---
            # After a successful calculation, update the cache with the new data.
            if self.cache is not None:
                pickled_obj = pickle.dumps(cacheable_obj)
                b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')

                new_cache_entry = {
                    "raw_pickle": b64_pickle,
                    mode: final_result_str # Store the format we just calculated
                }

                if base_str not in self.cache:
                    self.cache[base_str] = {}
                self.cache[base_str][expression] = new_cache_entry
                self.cache_dirty = True
                logging.debug(f"Populated cache for '{expression}' (base {base_str}).")

            return final_result_str

        except (AoPError, ValueError, TypeError, ZeroDivisionError) as e:
            return f"Error: {e}"
        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: An unexpected system error occurred."

    def _evaluate_symbolic_power_numerically(self, power_result: SymbolicPowerResult) -> AoPValue:
        """
        Evaluates a SymbolicPowerResult numerically using exponentiation by squaring.
        This function takes a SymbolicPowerResult and performs the actual
        exponentiation by squaring, returning a final AoPValue.
        This is where the "General Path" for __pow__ now lives.
        """
        from .aop_operations import _exponentiate_aop_value
        return _exponentiate_aop_value(power_result.base, power_result.exponent)

    def _load_cache(self):
        """Load the precalculated cache from file if available."""
        # --- MODIFIED: Use new cache filename ---
        cache_file = os.path.join('research', 'experiment_results', 'cache', CACHE_FILENAME)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cache: {e}")
                return {} # Return empty dict on failure
        return {} # Return empty dict if file doesn't exist

    # --- NEW: Method to save the cache if it has been modified ---
    def save_cache(self):
        """Saves the cache to file if it's dirty."""
        if not self.cache or not self.cache_dirty:
            logging.debug("Cache is clean. No save needed.")
            return

        cache_dir = os.path.join('research', 'experiment_results', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, CACHE_FILENAME)

        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logging.debug(f"Cache successfully saved to {cache_file}")
            self.cache_dirty = False
        except Exception as e:
            logging.error(f"Failed to save cache: {e}")
