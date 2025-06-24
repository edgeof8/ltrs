# aopl_python_impl/aop_calculator_cli.py
import sys
import argparse
import logging
from .aop_calculator import AoP_Calculator
from .definitions import OutputFormatMode

def main():
    # --- FINAL FIX: Improved help text to guide the user on shell quoting ---
    parser = argparse.ArgumentParser(
        description="Alphabet of Powers Calculator",
        epilog="NOTE: When using expressions with spaces, variables ($), or other special characters, "
               "enclose the entire expression in SINGLE QUOTES ('') to prevent the shell from "
               "interpreting them. Example: ltrs '$x = a+b'"
    )
    parser.add_argument("expression", type=str, help="The expression to evaluate.")
    parser.add_argument("--base", type=int, default=10, help="Numerical base for calculations (default: 10)")
    parser.add_argument("--mode", type=str, choices=["auto", "aop", "sci", "num"], default="auto", help="Output format mode (default: auto)")
    parser.add_argument("--precision", type=int, default=10, help="Precision for numerical output (default: 10)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='aop_calculator_debug.log', filemode='w')
        logging.debug("Debug mode enabled")
    else:
        # Clear the log file if not in debug mode to avoid confusion
        # with old errors.
        open('aop_calculator_debug.log', 'w').close()
        logging.basicConfig(level=logging.ERROR)

    mode_map = {
        "auto": OutputFormatMode.AUTO,
        "aop": OutputFormatMode.AOP,
        "sci": OutputFormatMode.SCIENTIFIC,
        "num": OutputFormatMode.NUMERICAL
    }

    calculator = AoP_Calculator(base=args.base)

    try:
        result = calculator.evaluate_expression(
            expression=args.expression,
            mode=mode_map[args.mode],
            precision=args.precision
        )
        if result.startswith("Error:"):
            print(result, file=sys.stderr)
            sys.exit(1)
        else:
            print(result)
    except Exception as e:
        logging.error(f"Unexpected system error: {str(e)}", exc_info=True)
        print(f"Unexpected system error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
