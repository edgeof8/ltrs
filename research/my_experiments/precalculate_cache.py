# Precalculation Cache Script for AoP Calculations
# Purpose: Precalculate a large tree of expressions from a^a to y^y for various bases
#          and store them in a rich cache format (AOP string, NUM string, and pickled object)
#          for extremely fast lookup during AoP calculations.

import os
import sys
import json
import pickle
import base64
from datetime import datetime

# Ensure the AoP library is in the path
# This assumes the script is run from the project root (e.g., `python research/scripts/precalculate_cache.py`)
# If run from its own directory, the path might need adjustment.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# --- MODIFIED: Import the specific components we need for manual pipeline execution ---
from aopl_python_impl.aop_parser import tokenize_expression, Parser
from aopl_python_impl.aop_operations import evaluate_ast
from aopl_python_impl.aop_formatter import format_as_aop, format_as_decimal_string
from aopl_python_impl.definitions import EXPONENT_TO_LETTER_MAP
from aopl_python_impl.aop_types import SymbolicPowerResult

# Configuration
BASES = [2, 10, 16]  # Common bases to precalculate for
VARIABLES = [chr(i) for i in range(ord('a'), ord('y') + 1)]  # Variables a to y
EXPONENTS = [chr(i) for i in range(ord('a'), ord('y') + 1)]  # Exponents a to y
CACHE_DIR = 'research/experiment_results/cache'

# --- MODIFIED: Use the new V2 cache filename to match the calculator ---
CACHE_FILENAME = 'precalculated_cache_v2.json'
CACHE_FILE = os.path.join(CACHE_DIR, CACHE_FILENAME)

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def process_task(task):
    """
    Process a single task for multiprocessing.
    This function now executes the full AoP pipeline manually to get the raw AoPValue object,
    then formats and pickles it to create a complete cache entry.
    """
    # Imports must be inside the worker function for some multiprocessing contexts
    from aopl_python_impl.aop_parser import tokenize_expression, Parser
    from aopl_python_impl.aop_operations import evaluate_ast
    from aopl_python_impl.aop_formatter import format_as_aop, format_as_decimal_string
    from aopl_python_impl.definitions import EXPONENT_TO_LETTER_MAP
    from aopl_python_impl.aop_types import SymbolicPowerResult
    import pickle
    import base64

    base, var, exp = task
    expr = f"{var}^{exp}"
    try:
        # 1. PARSE: Manually run the parser to get the AST
        tokens = tokenize_expression(expr)
        if not tokens:
            raise ValueError("Expression resulted in no tokens.")
        ast = Parser(tokens).parse()

        # 2. EVALUATE: Run the evaluator to get the final AoPValue or SymbolicPowerResult object
        #    We pass cache=None to ensure it performs a raw calculation, which is the point of this script.
        result_obj = evaluate_ast(ast, base, cache=None)

        # 3. FORMAT & SERIALIZE: Create all parts of the rich cache entry
        aop_str = format_as_aop(result_obj, EXPONENT_TO_LETTER_MAP)
        if isinstance(result_obj, SymbolicPowerResult):
            from aopl_python_impl.aop_calculator import AoP_Calculator
            calc = AoP_Calculator(base=base)
            result_aop_value = calc._evaluate_symbolic_power_numerically(result_obj)
        else:
            result_aop_value = result_obj
        num_str = format_as_decimal_string(result_aop_value)
        raw_pickle = base64.b64encode(pickle.dumps(result_obj)).decode('utf-8')

        # 4. ASSEMBLE: Create the final dictionary for the cache
        cache_entry = {
            "aop": aop_str,
            "num": num_str,
            "raw_pickle": raw_pickle
        }

        # Use the aop_str for the console output
        print(f"  Calculated {expr} for base={base} = {aop_str[:60]}..." if len(aop_str) > 60 else f"  Calculated {expr} for base={base} = {aop_str}")
        return base, expr, cache_entry

    except Exception as e:
        print(f"  Error calculating {expr} for base={base}: {e}")
        error_entry = {"error": str(e)}
        return base, expr, error_entry

def precalculate_expressions(existing_cache=None):
    """Precalculate expressions of the form var^exp for various bases using multiprocessing."""
    from multiprocessing import Pool, cpu_count

    cache = existing_cache if existing_cache else {}

    for base in BASES:
        base_str = str(base)
        if base_str not in cache:
            cache[base_str] = {}

        print(f"\nPrecalculating for base={base_str}...")

        # Create list of tasks for this base, skipping already calculated expressions
        tasks = [(base, var, exp) for var in VARIABLES for exp in EXPONENTS if f"{var}^{exp}" not in cache[base_str]]

        if not tasks:
            print(f"  All expressions for base={base_str} already calculated, skipping.")
            continue

        # Determine number of processes to use
        num_processes = min(len(tasks), cpu_count())
        print(f"  Found {len(tasks)} new expressions to calculate. Using {num_processes} processes.")

        # Run tasks in parallel
        with Pool(processes=num_processes) as pool:
            results = pool.map(process_task, tasks)

        # Collect results into cache. The logic here remains the same, but `result` is now a dictionary.
        for base_val, expr, result_entry in results:
            base_str_val = str(base_val)
            if base_str_val not in cache:
                cache[base_str_val] = {}
            cache[base_str_val][expr] = result_entry

        # Save cache after completing this base to prevent loss of progress
        save_cache(cache)
        print(f"  Cache updated and saved after completing base={base_str} calculations.")

    return cache

def save_cache(cache):
    """Save the precalculated cache to a file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"Cache saved to {CACHE_FILE}")

def load_cache():
    """Load the precalculated cache from a file if it exists."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode existing cache file at {CACHE_FILE}. Starting fresh.")
            return None
    return None

def main():
    print("--- AoP Pre-calculation Cache Generator ---")
    start_time = datetime.now()

    existing_cache = load_cache()
    if existing_cache:
        print(f"Existing cache loaded from {CACHE_FILE}. Updating with new calculations if necessary.")
        cache = precalculate_expressions(existing_cache)
    else:
        print(f"No existing cache found. Starting fresh precalculation.")
        cache = precalculate_expressions()

    # Final save just in case
    save_cache(cache)

    end_time = datetime.now()
    print(f"\nPrecalculation completed in {end_time - start_time}. Cache is ready for use.")

if __name__ == "__main__":
    main()
