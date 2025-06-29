# aopl_python_impl/aop_calculator_cli.py
import argparse
import sys
import logging
from .aop_calculator import AoP_Calculator
sys.set_int_max_str_digits(0)
def main():
    parser = argparse.ArgumentParser(description="AoP Calculator - Calculate expressions in various bases.")
    parser.add_argument("expression", type=str, help="The expression to evaluate (e.g., 'a^b + c').")
    parser.add_argument("--base", type=int, default=10, help="The base for calculation (default: 10).")
    parser.add_argument("--mode", choices=["num", "aop"], default="num", help="Output mode: 'num' for numerical, 'aop' for AoP notation (default: 'num').")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for detailed calculation trace.")
    # --- NEW: Argument to disable caching for testing/benchmarking ---
    parser.add_argument("--no-cache", action="store_true", help="Disable loading from and saving to the cache.")
    # --- NEW: Argument for file output ---
    parser.add_argument("-o", "--output", type=str, help="Path to an output file to write the result to.")
    args = parser.parse_args()

    if args.debug:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger()
        if logger.hasHandlers():
            logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    calc = AoP_Calculator(base=args.base)
    # --- MODIFIED: Conditionally disable cache object ---
    if args.no_cache:
        calc.cache = None

    try:
        result = calc.evaluate_expression(args.expression, mode=args.mode)

        if args.output:
            # Temporarily increase the digit limit ONLY for this file write operation
            # This is safer than setting it globally.
            original_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(0) # 0 = no limit for this specific task
                with open(args.output, 'w') as f:
                    f.write(result)
            finally:
                sys.set_int_max_str_digits(original_limit) # Always restore the original limit
            print(f"Result successfully written to: {args.output}")
        else:
            print(result)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

    # --- NEW: Save the cache to disk before exiting ---
    if not args.no_cache:
        calc.save_cache()

if __name__ == "__main__":
    main()
