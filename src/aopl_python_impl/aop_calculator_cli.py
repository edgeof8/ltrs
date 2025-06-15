# aopl_python_impl/aop_calculator_cli.py

import sys
import argparse
from .aop_calculator import AoPCalculator
from .definitions import OutputFormatMode

def main():
    parser = argparse.ArgumentParser(description="Alphabet of Powers Calculator")
    parser.add_argument("expression", type=str, help="The expression to evaluate")
    parser.add_argument("--base", type=int, default=10, help="Numerical base for calculations (default: 10)")
    parser.add_argument("--mode", type=str, choices=["auto", "aop", "sci", "num"], default="auto", help="Output format mode (default: auto)")
    parser.add_argument("--precision", type=int, default=10, help="Precision for numerical output (default: 10)")
    args = parser.parse_args()

    mode_map = {
        "auto": OutputFormatMode.AUTO,
        "aop": OutputFormatMode.AOP,
        "sci": OutputFormatMode.SCIENTIFIC,
        "num": OutputFormatMode.NUMERICAL
    }
    calculator = AoPCalculator(base=args.base, output_mode=mode_map[args.mode], precision=args.precision)

    try:
        result = calculator.calculate(args.expression)
        print(result)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
