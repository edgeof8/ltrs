# Precalculation Cache Script for AoP Calculations
# Purpose: Precalculate a large tree of expressions from a^a to z^z for various bases
#          and store them in a cache for quick lookup during AoP calculations.

import os
import sys
import json
from datetime import datetime

# Ensure the AoP library is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from aopl_python_impl.aop_calculator import AoP_Calculator

# Configuration
BASES = [2, 10]  # Common bases to precalculate for
VARIABLES = [chr(i) for i in range(ord('a'), ord('z') + 1)]  # Variables a to z
EXPONENTS = [chr(i) for i in range(ord('a'), ord('z') + 1)]  # Exponents a to z
CACHE_DIR = 'research/experiment_results/cache'
CACHE_FILE = os.path.join(CACHE_DIR, 'precalculated_values.json')

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def process_task(task):
    """Process a single task for multiprocessing."""
    from aopl_python_impl.aop_calculator import AoP_Calculator
    base, var, exp = task
    calculator = AoP_Calculator(base=base)
    expr = f"{var}^{exp}"
    try:
        result = calculator.evaluate_expression(expr, mode="aop")
        print(f"  Calculated {expr} for base={base} = {result[:50]}..." if len(str(result)) > 50 else f"  Calculated {expr} for base={base} = {result}")
        return base, expr, result
    except Exception as e:
        print(f"  Error calculating {expr} for base={base}: {e}")
        return base, expr, str(e)

def precalculate_expressions():
    """Precalculate expressions of the form var^exp for various bases using multiprocessing."""
    from multiprocessing import Pool, cpu_count
    cache = {}

    for base in BASES:
        cache[base] = {}
        print(f"Precalculating for base={base}...")
        # Create list of tasks for this base
        tasks = [(base, var, exp) for var in VARIABLES for exp in EXPONENTS]
        # Determine number of processes to use
        num_processes = min(len(tasks), cpu_count())
        print(f"  Using {num_processes} processes to maximize CPU usage.")
        # Run tasks in parallel
        with Pool(processes=num_processes) as pool:
            results = pool.map(process_task, tasks)
        # Collect results into cache
        for base, expr, result in results:
            cache[base][expr] = result

    return cache

def save_cache(cache):
    """Save the precalculated cache to a file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"Cache saved to {CACHE_FILE}")

def load_cache():
    """Load the precalculated cache from a file if it exists."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None

def main():
    # Check if cache already exists
    existing_cache = load_cache()
    if existing_cache:
        print("Existing cache loaded. Updating with new calculations if necessary.")
        cache = existing_cache
    else:
        print("No existing cache found. Starting fresh precalculation.")
        cache = precalculate_expressions()

    # Save the updated cache
    save_cache(cache)
    print("Precalculation completed. Cache is ready for use in AoP calculations.")

if __name__ == "__main__":
    main()
