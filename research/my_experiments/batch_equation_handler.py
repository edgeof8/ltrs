"""
Batch Equation Handler for AoP Calculator

This script automates the execution of multiple equations using the Alphabet of Powers (AoP) calculator CLI tool 'ltrs'.
It runs a predefined list of expressions across specified bases, captures the output, and saves the results to a file.
This is useful for batch processing equations without manual command-line input for each one.

Usage:
    python batch_equation_handler.py [output_file]
    If no output file is specified, results are saved to 'batch_equation_results.txt' in the current directory.
"""

import subprocess
import sys
import datetime

def run_ltrs_expression(expression, base=10, mode="auto", precision=10, debug=False):
    """
    Run a single expression through the ltrs CLI tool and return the output.

    Args:
        expression (str): The mathematical expression to evaluate.
        base (int/float): The numerical base for the calculation.
        mode (str): Output formatting mode (auto, aop, sci, num).
        precision (int): Decimal precision for output.
        debug (bool): Whether to enable debug output.

    Returns:
        str: The output from the ltrs command or an error message.
    """
    try:
        # Construct the command with arguments as separate list elements
        cmd = ["python", "-m", "aopl_python_impl.aop_calculator_cli", expression, "--base", str(base), "--mode", mode, "--precision", str(precision)]
        if debug:
            cmd.append("--debug")

        # Run the command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def main():
    # Default output file if not specified
    output_file = sys.argv[1] if len(sys.argv) > 1 else "batch_equation_results.txt"

    # List of expressions to evaluate (can be extended)
    expressions = [
        "j^j",
        "j^j^j",
        "j^(j^j) + j * j^j",
        "(j^j) * j + j^j",
        "Z^Z",
        "Z^Z^Z",
        "Z^Z^Z^Z",
        "sqrt(j^j)",
        "log(j^j)",
        "sin(#pi/2) + log(a)"
    ]

    # List of bases to test each expression with
    bases = [10, 2]  # Base 10, Base 2

    # Header for the results
    results = [f"Batch Equation Results - Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    results.append("=" * 80)
    results.append("")

    # Process each expression with each base
    for expr in expressions:
        results.append(f"Expression: {expr}")
        results.append("-" * 40)
        for base in bases:
            output = run_ltrs_expression(expr, base=base)
            results.append(f"Base {base}: {output}")
        results.append("")

    # Write results to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(results))
        print(f"Results successfully saved to {output_file}")
    except Exception as e:
        print(f"Failed to write results to {output_file}: {str(e)}")
        print("\nPrinting results to console instead:")
        print("\n".join(results))

if __name__ == "__main__":
    main()
