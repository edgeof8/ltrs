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
# --- Note: Removed specific PyO3 exception import due to unresolved import issue ---
# Using a more generic exception handling approach instead.
from .aop_logger import print_legend, log_eval_report_start, log_pow
from .aop_value import AoPValue # Import AoPValue for type hints and unpickling

# --- NEW: Define a new cache filename to avoid conflicts with the old format ---
CACHE_FILENAME = 'precalculated_cache_v2.json'

def _resolve_power(self: SymbolicPowerResult) -> AoPValue:
    """
    The EAGER power evaluator. This is the single entry point for all
    numerical power calculations. It analyzes the base and exponent
    and chooses the most efficient path.
    """
    base_val = self.base.resolve() if isinstance(self.base, SymbolicPowerResult) else self.base
    exp_val = self.exponent.resolve() if isinstance(self.exponent, SymbolicPowerResult) else self.exponent

    if not isinstance(base_val, AoPValue) or not isinstance(exp_val, AoPValue):
        raise TypeError("Cannot resolve power on non-AoPValue types.")

    # With the Rust core enabled, the __pow__ method handles all logic,
    # including any symbolic shortcuts. We simply call it.
    return base_val ** exp_val

# Add the resolve method to the SymbolicPowerResult class dynamically
SymbolicPowerResult.resolve = _resolve_power

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

            if self.cache and base_str in self.cache and expression in self.cache[base_str]:
                cached_data = self.cache[base_str][expression]
                logging.debug(f"Cache hit for '{expression}' (base {base_str}). Cached data: {list(cached_data.keys())}")

                if mode in cached_data:
                    logging.debug(f"Returning pre-formatted '{mode}' from cache.")
                    return cached_data[mode]

                if "raw_pickle" in cached_data:
                    logging.debug("Unpickling AoPValue from cache to generate new format.")
                    pickle_data = base64.b64decode(cached_data["raw_pickle"])
                    result_obj = pickle.loads(pickle_data)

                    # Format the unpickled object into the desired mode
                    if mode == "aop":
                        # Use the main formatter which can handle both AoPValue and SymbolicPowerResult
                        formatted_result = format_as_aop(result_obj, EXPONENT_TO_LETTER_MAP)
                    else: # "num"
                        # to_numerical will fail on SymbolicPowerResult, so we must resolve first.
                        # This path is for when we have a raw object but not the specific format.
                        resolved_val = self._resolve_to_value(result_obj)
                        if isinstance(resolved_val, SymbolicPowerResult):
                            return "Error: Result is symbolic and has no numerical value."
                        formatted_result = format_as_decimal_string(resolved_val)

                    self.cache[base_str][expression][mode] = formatted_result
                    self.cache_dirty = True
                    return formatted_result

            logging.debug(f"Cache miss for '{expression}' (base {base_str}). Computing from scratch.")
            tokens = tokenize_expression(expression)
            if not tokens: return ""
            parser = Parser(tokens)
            ast = parser.parse()

            log_eval_report_start(repr(ast))
            result_obj = evaluate_ast(ast, self.base, self.cache)

            # The final object might be an AoPValue or an unresolvable SymbolicPowerResult
            final_obj = self._resolve_to_value(result_obj)

            if mode == "aop":
                final_result_str = format_as_aop(final_obj, EXPONENT_TO_LETTER_MAP)
            else: # "num" mode
                # If the final object is still symbolic, numerical conversion is impossible.
                if isinstance(final_obj, SymbolicPowerResult):
                    return "Error: Result is symbolic and has no numerical value."
                final_result_str = format_as_decimal_string(final_obj)

            cacheable_obj = final_obj # Cache the final object, whatever its type

            if self.cache is not None:
                pickled_obj = pickle.dumps(cacheable_obj)
                b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')

                new_cache_entry = { "raw_pickle": b64_pickle, mode: final_result_str }

                if base_str not in self.cache: self.cache[base_str] = {}
                self.cache[base_str][expression] = new_cache_entry
                self.cache_dirty = True
                logging.debug(f"Populated cache for '{expression}' (base {base_str}).")

            return final_result_str

        except (AoPError, ValueError, TypeError, ZeroDivisionError) as e:
            return f"Error: {e}"
        except Exception as e:
            logging.error("Unexpected error in calculation", exc_info=True)
            return f"Error: An unexpected system error occurred: {type(e).__name__}"

    def _resolve_to_value(self, obj: object) -> 'AoPValue | SymbolicPowerResult':
        """Recursively resolves an object into a final AoPValue or leaves it as a SymbolicPowerResult if unresolvable."""
        if isinstance(obj, AoPValue):
            return obj

        if isinstance(obj, SymbolicPowerResult):
            log_pow(f"Resolving SymbolicPower: {obj!r}")

            resolved_base = self._resolve_to_value(obj.base)
            resolved_exponent = self._resolve_to_value(obj.exponent)

            # If either part is still symbolic, we can't proceed.
            if isinstance(resolved_base, SymbolicPowerResult) or isinstance(resolved_exponent, SymbolicPowerResult):
                return SymbolicPowerResult(resolved_base, resolved_exponent)

            try:
                # Attempt the power operation only if both are AoPValue.
                if isinstance(resolved_base, AoPValue) and isinstance(resolved_exponent, AoPValue):
                    result = resolved_base ** resolved_exponent
                    return result
                else:
                    # If not both AoPValue, return symbolic result without attempting operation.
                    log_pow(f"Power operation skipped due to non-AoPValue types. Returning unevaluated: {obj!r}")
                    return SymbolicPowerResult(resolved_base, resolved_exponent)
            except Exception as e:
                # --- CRITICAL FIX ---
                # Catch any exception from the power operation, assuming it's unresolvable (e.g., complex^symbolic).
                # In this case, we do not fail. We return the unevaluated symbolic object.
                log_pow(f"Power operation failed with error: {e}. Returning unevaluated: {obj!r}")
                return SymbolicPowerResult(resolved_base, resolved_exponent)

        raise TypeError(f"Cannot resolve unexpected type: {type(obj)}")

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
