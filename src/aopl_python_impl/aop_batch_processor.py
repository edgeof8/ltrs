# aop_batch_processor.py
import argparse
import sys
import os # For path joining
from aopl_python_impl.aop_calculator import AoP_Calculator # Corrected path assuming src is in PYTHONPATH or similar
from aopl_python_impl.definitions import OutputFormatMode

# If aopl_python_impl is not directly in PYTHONPATH, adjust sys.path
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.dirname(current_dir) # Assuming this script is in a 'scripts' folder one level down from project root
# sys.path.insert(0, project_root)
# from aopl_python_impl.aop_calculator import AoP_Calculator
# from aopl_python_impl.definitions import OutputFormatMode


def process_batch(input_filepath: str, output_filepath: str, base: int, mode: str, precision: int):
    """
    Reads expressions from input_file, evaluates them using multiprocessing, and writes results to output_file.
    """
    from multiprocessing import Pool
    from functools import partial

    calculator = AoP_Calculator(base=base) # Initialize calculator with base

    mode_map = {
        "auto": OutputFormatMode.AUTO,
        "aop": OutputFormatMode.AOP,
        "sci": OutputFormatMode.SCIENTIFIC,
        "num": OutputFormatMode.NUMERICAL
    }
    output_mode = mode_map.get(mode.lower(), OutputFormatMode.AUTO)

    results_output = []
    expressions = []

    try:
        with open(input_filepath, 'r') as infile:
            for line_num, line in enumerate(infile, 1):
                expression = line.strip()
                if not expression or expression.startswith('#'): # Skip empty lines or comments
                    results_output.append(f"Skipped line {line_num}: {expression}")
                    continue
                expressions.append((line_num, expression))

        if expressions:
            # Function to evaluate a single expression
            def evaluate_single_expression(args, calc_base=base, calc_mode=output_mode):
                line_num, expr = args
                try:
                    calc = AoP_Calculator(base=calc_base)
                    # Map OutputFormatMode back to string
                    mode_str = {
                        OutputFormatMode.AUTO: "auto",
                        OutputFormatMode.AOP: "aop",
                        OutputFormatMode.SCIENTIFIC: "sci",
                        OutputFormatMode.NUMERICAL: "num"
                    }.get(calc_mode, "num")
                    result_str = calc.evaluate_expression(
                        expression=expr,
                        mode=mode_str
                    )
                    return f"Input: {expr}\nOutput: {result_str}\n---"
                except Exception as e:
                    return f"Input: {expr}\nError: Unhandled exception during evaluation: {type(e).__name__}: {e}\n---"

            # Use multiprocessing Pool to parallelize expression evaluation
            with Pool() as pool:
                results = pool.map(evaluate_single_expression, expressions)
                results_output.extend(results)

    except FileNotFoundError:
        results_output.append(f"Error: Input file not found: {input_filepath}")
    except Exception as e:
        results_output.append(f"Error: General batch processing error: {type(e).__name__}: {e}")

    try:
        with open(output_filepath, 'w') as outfile:
            for res_line in results_output:
                outfile.write(res_line + "\n")
        print(f"Batch processing complete. Results in: {output_filepath}")
    except IOError:
        print(f"Error: Could not write to output file: {output_filepath}")
        print("Results:")
        for res_line in results_output:
            print(res_line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AoP Batch Calculator Processor")
    parser.add_argument("inputfile", help="Path to the input file with expressions (one per line).")
    parser.add_argument("outputfile", help="Path to the output file for results.")
    parser.add_argument("--base", type=int, default=10, help="Numerical base for calculations (default: 10)")
    parser.add_argument("--mode", type=str, choices=["auto", "aop", "sci", "num"], default="auto", help="Output format mode (default: auto)")
    parser.add_argument("--precision", type=int, default=10, help="Precision for numerical output (default: 10)")
    # No --debug flag here, as it's for the AI to consume clean output. Internal logging can still be active.

    args = parser.parse_args()

    process_batch(args.inputfile, args.outputfile, args.base, args.mode, args.precision)
