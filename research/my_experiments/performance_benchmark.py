# Performance Benchmarking Script for AoP Hyper-Power Calculations
# Adapted from research/experiment_templates/automated_testing.py
# Purpose: Measure execution times for hyper-power expressions across various depths and bases

import subprocess
import time
import csv
import os

# Configuration
BASES = [2, 10]  # Integer bases as per AoP CLI requirements
DEPTHS = range(5, 11)  # Depths from 5 to 10 for hyper-power towers
LETTER = 'j'  # Letter representing a large exponent (base^10 by default in base 10)
OUTPUT_FILE = 'research/experiment_results/hyperpower_performance_metrics.csv'

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Function to generate hyper-power expression string for a given depth
def generate_expression(depth, letter=LETTER):
    return '^'.join([letter] * depth)

# Function to run a single command and measure execution time
def run_command(expression, base):
    cmd = f'ltrs "{expression}" --base {base}'
    start_time = time.time()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        end_time = time.time()
        execution_time = end_time - start_time
        if result.returncode == 0:
            return execution_time, result.stdout.strip(), 'Success'
        else:
            return execution_time, result.stderr.strip(), 'Error'
    except subprocess.TimeoutExpired:
        end_time = time.time()
        return end_time - start_time, 'Timeout after 60 seconds', 'Timeout'
    except Exception as e:
        end_time = time.time()
        return end_time - start_time, str(e), 'Exception'

# Main benchmarking loop
def main():
    # Prepare CSV file for results
    with open(OUTPUT_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Base', 'Depth', 'Expression', 'Execution Time (s)', 'Output', 'Status'])

        print("Starting performance benchmarking for AoP hyper-power calculations...")
        for base in BASES:
            for depth in DEPTHS:
                expression = generate_expression(depth)
                print(f"Testing base={base}, depth={depth}, expression={expression}")
                exec_time, output, status = run_command(expression, base)
                writer.writerow([base, depth, expression, exec_time, output, status])
                print(f"  Result: Time={exec_time:.4f}s, Status={status}")

    print(f"Benchmarking complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
