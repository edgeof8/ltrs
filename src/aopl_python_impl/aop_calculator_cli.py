# aopl_python_impl/aop_calculator_cli.py
import argparse
import sys
import logging
from .aop_calculator import AoP_Calculator

def main():
    parser = argparse.ArgumentParser(description="AoP Calculator - Calculate expressions in various bases.")
    parser.add_argument("expression", type=str, help="The expression to evaluate (e.g., 'a^b + c').")
    parser.add_argument("--base", type=int, default=10, help="The base for calculation (default: 10).")
    parser.add_argument("--mode", choices=["num", "aop"], default="num", help="Output mode: 'num' for numerical, 'aop' for AoP notation (default: 'num').")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for detailed calculation trace.")
    # --- NEW: Argument to disable caching for testing/benchmarking ---
    parser.add_argument("--no-cache", action="store_true", help="Disable loading from and saving to the cache.")
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

    result = calc.evaluate_expression(args.expression, mode=args.mode)
    print(result)

    # --- NEW: Save the cache to disk before exiting ---
    if not args.no_cache:
        calc.save_cache()

if __name__ == "__main__":
    main()
