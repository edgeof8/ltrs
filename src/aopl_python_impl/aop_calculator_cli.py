# aopl_python_impl/aop_calculator_cli.py
import argparse
import sys
import logging
from .aop_calculator import AoP_Calculator
# Import the new setup function
from .aop_logger import enable_explainer

sys.set_int_max_str_digits(0)

def main():
    parser = argparse.ArgumentParser(description="AoP Calculator - Calculate expressions in various bases.")
    parser.add_argument("expression", type=str, help="The expression to evaluate (e.g., 'a^b + c').")
    parser.add_argument("--base", type=int, default=10, help="The base for calculation (default: 10).")
    parser.add_argument("--mode", choices=["num", "aop"], default="num", help="Output mode: 'num' for numerical, 'aop' for AoP notation (default: 'num').")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for detailed calculation trace.")
    parser.add_argument("--no-cache", action="store_true", help="Disable loading from and saving to the cache.")
    parser.add_argument("-o", "--output", type=str, help="Path to an output file to write the result to.")
    args = parser.parse_args()

    # If --debug is passed, enable the explainer globally
    if args.debug:
        enable_explainer()

    calc = AoP_Calculator(base=args.base)
    if args.no_cache:
        calc.cache = None

    try:
        result = calc.evaluate_expression(args.expression, mode=args.mode)

        if args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(result)
                print(f"Result successfully written to: {args.output}")
            except IOError as e:
                logging.error(f"Could not write to output file: {e}")
        else:
            print(result)

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=args.debug)

    if not args.no_cache:
        calc.save_cache()

if __name__ == "__main__":
    main()
