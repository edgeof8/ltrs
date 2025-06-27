# aopl_python_impl/aop_calculator_cli.py
import sys, argparse, logging, os

# This is a hack to make the imports work when running as a module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.aopl_python_impl.aop_calculator import AoP_Calculator

def main():
    # --- FINAL CONFIGURATION: Unleash the power ---
    # Increase Python's limit for integer-to-string conversion.
    # Set to 0 for no limit.
    sys.set_int_max_str_digits(0)

    parser = argparse.ArgumentParser(description="Alphabet of Powers Calculator")
    parser.add_argument("expression", type=str, help="The expression to evaluate. Use '--' for expressions starting with a hyphen.")
    parser.add_argument("--base", type=int, default=10, help="Numerical base (default: 10)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
        logging.debug("Debug mode enabled")
    else:
        logging.basicConfig(level=logging.WARNING)

    calculator = AoP_Calculator(base=args.base)
    result = calculator.evaluate_expression(expression=args.expression)

    if result.startswith("Error:"):
        print(result, file=sys.stderr)
        sys.exit(1)
    else:
        print(result)

if __name__ == "__main__":
    main()
