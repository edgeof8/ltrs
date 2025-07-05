# profile_small_power.py

import cProfile
import pstats
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from aopl_python_impl.aop_value import AoPValue

def profile_small_exponentiation():
    print("--- Starting Profiling for (5a+2b+6)^123 ---")

    base_val = AoPValue.from_number(256, 10) # 2c + 5b + 6
    exponent_val = AoPValue.from_number(123, 10)

    print(f"Profiling: {base_val!r} ** {exponent_val!r}")

    start_time = time.perf_counter()
    final_result = base_val ** exponent_val
    end_time = time.perf_counter()

    print("--- Profiling Complete ---")
    print(f"Calculation took: {end_time - start_time:.4f} seconds")
    print(f"Result has {len(final_result.poly)} terms.")

if __name__ == "__main__":
    profile_small_exponentiation()
