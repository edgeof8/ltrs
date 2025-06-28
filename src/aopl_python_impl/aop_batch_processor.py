# aop_batch_processor.py
import argparse
import sys
import os
from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.definitions import OutputFormatMode

# --- NEW: Global variable for the calculator instance within each worker process ---
worker_calculator = None

# --- NEW: Initializer function for the multiprocessing pool ---
def init_worker(base: int):
    """
    This function is called once for each worker process.
    It creates a single AoP_Calculator instance for that process.
    """
    global worker_calculator
    print(f"Initializing calculator in process {os.getpid()}...") # Optional: for seeing it work
    # Each worker gets its own calculator, with its own cache.
    # The --no-cache flag will be respected here.
    worker_calculator = AoP_Calculator(base=base)
    # If the CLI says no-cache, disable it in the worker.
    if cli_args.no_cache:
        worker_calculator.cache = None

# --- MODIFIED: The main worker function that processes a single expression ---
def evaluate_single_expression(args):
    """
    Evaluates a single expression using the process-local calculator.
    """
    global worker_calculator
    line_num, expr, mode_str = args

    # The worker_calculator should have been initialized by the pool's initializer
    if worker_calculator is None:
        return f"Input: {expr}\nError: Worker process was not initialized correctly.\n---"

    try:
        result_str = worker_calculator.evaluate_expression(
            expression=expr,
            mode=mode_str
        )
        return f"Input: {expr}\nOutput: {result_str}\n---"
    except Exception as e:
        return f"Input: {expr}\nError: Unhandled exception during evaluation: {type(e).__name__}: {e}\n---"

# --- MODIFIED: The main batch processing logic ---
def process_batch(input_filepath: str, output_filepath: str, base: int, mode: str):
    """
    Reads expressions from input_file, evaluates them using an efficient
    multiprocessing pool, and writes results to output_file.
    """
    from multiprocessing import Pool, cpu_count

    # This top-level calculator is primarily for saving the final merged cache.
    # The actual computation happens in the worker processes.
    main_calculator = AoP_Calculator(base=base)
    if cli_args.no_cache:
        main_calculator.cache = None

    results_output = []
    expressions_to_process = []

    try:
        with open(input_filepath, 'r') as infile:
            for line_num, line in enumerate(infile, 1):
                expression = line.strip()
                if not expression or expression.startswith('#'):
                    continue
                # Package all necessary arguments for the worker function
                expressions_to_process.append((line_num, expression, mode))

        if expressions_to_process:
            # Determine a reasonable number of processes
            num_processes = min(cpu_count(), len(expressions_to_process))

            # Use the initializer to set up each worker process efficiently
            with Pool(processes=num_processes, initializer=init_worker, initargs=(base,)) as pool:
                # map will chunk the expressions_to_process list and distribute
                # the chunks to the worker processes.
                results = pool.map(evaluate_single_expression, expressions_to_process)
                results_output.extend(results)

            # NOTE: Merging caches from multiple processes back into the main one is complex.
            # For simplicity, this version does not do that. The main benefit gained
            # is the reuse of the calculator *within* each worker's task chunk, which
            # prevents the massive overhead of re-initialization for every single line.
            # A true shared cache would require a more complex setup (e.g., Manager process).
            # The current approach is a major and sufficient performance improvement.

    except FileNotFoundError:
        results_output.append(f"Error: Input file not found: {input_filepath}")
    except Exception as e:
        results_output.append(f"Error: General batch processing error: {type(e).__name__}: {e}")

    # Write results to file
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

# --- MODIFIED: Main execution block to handle arguments ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AoP Batch Calculator Processor")
    parser.add_argument("inputfile", help="Path to the input file with expressions (one per line).")
    parser.add_argument("outputfile", help="Path to the output file for results.")
    parser.add_argument("--base", type=int, default=10, help="Numerical base for calculations (default: 10)")
    parser.add_argument("--mode", type=str, choices=["num", "aop"], default="num", help="Output format mode (default: 'num').")
    # --- ADDED: Make the no-cache flag available ---
    parser.add_argument("--no-cache", action="store_true", help="Disable loading from and saving to the cache.")

    # Store args in a global variable to be accessible by the initializer
    cli_args = parser.parse_args()

    # We no longer need to pass precision, as the main calculator handles it
    process_batch(cli_args.inputfile, cli_args.outputfile, cli_args.base, cli_args.mode)
