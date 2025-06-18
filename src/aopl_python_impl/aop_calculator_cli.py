# aopl_python_impl/aop_calculator_cli.py

import sys
import argparse
import logging
from .aop_calculator import AoP_Calculator
from .definitions import OutputFormatMode

def main():
    parser = argparse.ArgumentParser(description="Alphabet of Powers Calculator")
    parser.add_argument("expression", type=str, help="The expression to evaluate")
    parser.add_argument("--base", type=int, default=10, help="Numerical base for calculations (default: 10)")
    parser.add_argument("--mode", type=str, choices=["auto", "aop", "sci", "num"], default="auto", help="Output format mode (default: auto)")
    parser.add_argument("--precision", type=int, default=10, help="Precision for numerical output (default: 10)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Setup logging if debug is enabled
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='aop_calculator_debug.log')
        logging.debug("Debug mode enabled")
    else:
        logging.basicConfig(level=logging.ERROR)

    mode_map = {
        "auto": OutputFormatMode.AUTO,
        "aop": OutputFormatMode.AOP,
        "sci": OutputFormatMode.SCIENTIFIC,
        "num": OutputFormatMode.NUMERICAL
    }
    calculator = AoP_Calculator(base=args.base, output_format_mode=mode_map[args.mode], precision=args.precision)

    try:
        result = calculator.evaluate_expression(args.expression)
        if result.startswith("Error:"):
            print(result, file=sys.stderr) # Print the specific error to stderr
            sys.exit(1) # Exit with error code
        else:
            print(result) # Print successful result to stdout
    except Exception as e: # Catch any other unexpected exceptions
        logging.error(f"Unexpected system error: {str(e)}", exc_info=True)
        print(f"Unexpected system error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
