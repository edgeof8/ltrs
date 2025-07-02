import cProfile
import pstats
import sys
import os

# Add the source directory to the Python path to make imports work
# This assumes the script is run from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from aopl_python_impl.aop_value import AoPValue

def profile_heavy_exponentiation():
    """
    This function isolates and runs a demanding exponentiation operation
    to fairly test the performance of the final Rust-accelerated engine.
    """
    print("--- Starting Profiling for (b2a)^2d ---")
    print("This is equivalent to (120)^20000.")

    # Create the base: b2a = 120
    base_val = AoPValue.from_number(120, 10)

    # Create a much larger exponent to properly test the Rust core:
    # 2d = 20000
    exponent_val = AoPValue.from_number(20000, 10)

    print(f"Profiling: {base_val!r} ** {exponent_val!r}")

    # Use the public `**` operator for a fair, real-world test.
    # This calls the __pow__ method, which delegates directly to the Rust core.
    final_result = base_val ** exponent_val

    print("--- Profiling Complete ---")
    # We print a small part of the result to confirm it worked.
    print(f"Result has {len(final_result.poly)} terms.")


def main():
    # Set up the profiler
    profiler = cProfile.Profile()
    profiler.enable()

    # Run the function we want to profile
    profile_heavy_exponentiation()

    profiler.disable()

    # Print the stats
    print("\n--- Profiler Results ---")
    # Sort stats by 'cumulative time' to see the biggest time sinks
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20) # Print the top 20 most time-consuming functions

if __name__ == "__main__":
    main()
