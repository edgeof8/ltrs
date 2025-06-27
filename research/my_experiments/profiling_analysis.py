# Profiling Analysis Script for AoP Calculations
# Purpose: Use cProfile to analyze where time is spent during the execution of AoP calculations
#          for specific expressions, providing detailed performance data on internal function calls.

import cProfile
import pstats
import os
import sys
import csv
import psutil
import time
from datetime import datetime

# Ensure the AoP library is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.aop_parser import Parser, tokenize_expression
from aopl_python_impl.aop_operations import evaluate_ast

# Configuration
EXPRESSIONS = ["j^a", "j^b", "j^c", "j^d", "j^e", "j^f", "j^g", "j^a + j^b + j^c", "j^d + j^e + j^a", "j^a + j^b + j^c + j^d + j^e + j^f"]  # Reduced set of expressions, excluding the most time-consuming test case
BASES = [2, 10]  # Integer bases as per AoP CLI requirements
OUTPUT_DIR = 'research/experiment_results'
PROFILE_REPORT_FILE = os.path.join(OUTPUT_DIR, 'aop_profiling_report_{}.txt')
CSV_OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'aop_profiling_metrics.csv')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_profiling(expression, base):
    """Run profiling for a given expression and base, including CPU usage metrics."""
    calculator = AoP_Calculator(base=base)
    tokens = tokenize_expression(expression)
    parser = Parser(tokens)

    # Parse the expression
    parsed_expr = parser.parse()

    # Monitor CPU usage
    cpu_start = psutil.cpu_percent(interval=None)
    start_time = time.time()

    # Profile the calculation
    profiler = cProfile.Profile()
    profiler.enable()

    # Execute the calculation
    result = calculator.evaluate_expression(expression, mode="aop")

    profiler.disable()

    end_time = time.time()
    cpu_end = psutil.cpu_percent(interval=None)
    cpu_avg = (cpu_start + cpu_end) / 2  # Rough average of CPU usage during execution
    duration = end_time - start_time

    # Generate a unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    profile_report_path = PROFILE_REPORT_FILE.format(f"{expression.replace('^', '_')}_base_{base}_{timestamp}")

    # Save profiling stats to a detailed report
    with open(profile_report_path, 'w') as f:
        ps = pstats.Stats(profiler, stream=f)
        ps.sort_stats('cumulative')
        ps.print_stats()

    # Extract key metrics for CSV output (top 10 cumulative time)
    ps = pstats.Stats(profiler)
    ps.sort_stats(pstats.SortKey.CUMULATIVE)

    metrics = []
    import uuid

    # Use a unique temporary file to store stats for each process
    temp_file = f"temp_stats_{uuid.uuid4()}.txt"
    with open(temp_file, 'w') as f:
        ps = pstats.Stats(profiler, stream=f)
        ps.sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats(10)

    # Read the top 10 functions from the temporary file (this is a workaround for direct access)
    with open(temp_file, 'r') as f:
        lines = f.readlines()
        for line in lines[:10]:
            parts = line.split()
            if len(parts) >= 5:
                try:
                    func_name = parts[-1]
                    cumulative_time = float(parts[3])
                    calls = int(parts[0])
                    metrics.append({
                        'function': func_name,
                        'cumulative_time': cumulative_time,
                        'calls': calls,
                        'time_per_call': cumulative_time / calls if calls > 0 else 0
                    })
                except (ValueError, IndexError):
                    continue

    try:
        os.remove(temp_file) if os.path.exists(temp_file) else None
    except PermissionError:
        pass  # Ignore permission errors if file is still in use by another process

    return result, profile_report_path, metrics, cpu_avg, duration

def process_task(task):
    """Process a single profiling task for an expression and base."""
    expr, base = task
    print(f"Profiling {expr} with base={base}...")
    result, report_path, metrics, cpu_usage, duration = run_profiling(expr, base)

    # Prepare data to return for CSV writing
    csv_rows = []
    for metric in metrics:
        csv_rows.append({
            'Expression': expr,
            'Base': base,
            'Function': metric['function'],
            'Cumulative Time (s)': metric['cumulative_time'],
            'Calls': metric['calls'],
            'Time per Call (s)': metric['time_per_call'],
            'Profile Report Path': report_path,
            'CPU Usage (%)': cpu_usage if metric == metrics[0] else '',
            'Duration (s)': duration if metric == metrics[0] else ''
        })

    print(f"  Completed profiling. Detailed report saved to {report_path}")
    print(f"  CPU Usage: {cpu_usage:.1f}% | Duration: {duration:.2f}s")
    print(f"  Result: {result[:100]}..." if len(str(result)) > 100 else f"  Result: {result}")

    return csv_rows

def main():
    from multiprocessing import Pool, cpu_count

    # Prepare CSV file for profiling metrics
    with open(CSV_OUTPUT_FILE, mode='w', newline='') as csv_file:
        fieldnames = ['Expression', 'Base', 'Function', 'Cumulative Time (s)', 'Calls', 'Time per Call (s)', 'Profile Report Path', 'CPU Usage (%)', 'Duration (s)']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        print("Starting detailed profiling analysis for AoP calculations...")

        # Determine number of processes to use, aiming to maximize CPU usage
        num_processes = min(len(EXPRESSIONS) * len(BASES), cpu_count())
        print(f"Using {num_processes} processes to maximize CPU usage.")

        # Create list of tasks (expression, base pairs)
        tasks = [(expr, base) for base in BASES for expr in EXPRESSIONS]

        # Run tasks in parallel
        with Pool(processes=num_processes) as pool:
            all_results = pool.map(process_task, tasks)

        # Write all results to CSV
        with open(CSV_OUTPUT_FILE, mode='a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            for result_rows in all_results:
                for row in result_rows:
                    writer.writerow(row)

        print(f"Profiling metrics saved to {CSV_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
