# Enhanced Performance Benchmarking Script for AoP Hyper-Power Calculations
# Adapted from research/my_experiments/performance_benchmark.py
# Purpose: Measure execution times for hyper-power and other expressions across various depths and bases,
#          while ensuring correctness of calculations through validation against expected results.

import subprocess
import time
import csv
import os
import json

# Configuration
BASES = [2, 10]  # Integer bases as per AoP CLI requirements
EXPRESSIONS = ["j^a", "j^b", "j^c"]  # Simpler expressions for faster hyper-power tests
ITERATIONS = 5  # Number of iterations for more accurate timing data
LETTER = 'j'  # Letter representing a large exponent (base^10 by default in base 10)
OUTPUT_FILE = 'research/experiment_results/enhanced_hyperpower_performance_metrics.csv'
TEST_CASES_FILE = 'research/my_experiments/test_cases.json'

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
os.makedirs(os.path.dirname(TEST_CASES_FILE), exist_ok=True)

# Predefined test cases with expected outputs for correctness validation
# These are basic expressions to ensure core functionality; expand as needed
TEST_CASES = {
    "basic_addition": {"expression": "2+3", "expected_output": "5", "base": 10},
    "basic_multiplication": {"expression": "4*5", "expected_output": "20", "base": 10},
    "basic_exponentiation": {"expression": "2^3", "expected_output": "8", "base": 10},
    "symbolic_aop": {"expression": "(a+b)(a-b)", "expected_output": "-9c - 9b", "base": 10, "mode": "aop"},
    "large_number": {"expression": "j^2", "expected_output": "100000000000000000000", "base": 10}
}

# Save test cases to a file for future reference or expansion
if not os.path.exists(TEST_CASES_FILE):
    with open(TEST_CASES_FILE, 'w') as f:
        json.dump(TEST_CASES, f, indent=2)

# Function to get the expression for testing (not used for predefined expressions)
def generate_expression(depth, letter=LETTER):
    return '^'.join([letter] * depth)

# Function to run a single command and measure execution time over multiple iterations
def run_command(expression, base, mode="aop", iterations=ITERATIONS):
    cmd = f'ltrs "{expression}" --base {base}'
    if mode == "aop":
        cmd += " --mode aop"
    total_time = 0.0
    status = 'Success'
    output = ''
    for _ in range(iterations):
        start_time = time.time()
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            end_time = time.time()
            total_time += (end_time - start_time)
            if result.returncode != 0:
                status = 'Error'
                output = result.stderr.strip()
                break
            else:
                output = result.stdout.strip()
        except subprocess.TimeoutExpired:
            end_time = time.time()
            total_time += (end_time - start_time)
            status = 'Timeout'
            output = 'Timeout after 30 seconds'
            break
        except Exception as e:
            end_time = time.time()
            total_time += (end_time - start_time)
            status = 'Exception'
            output = str(e)
            break
    average_time = total_time / iterations
    return average_time, output, status

# Function to validate output against expected result
def validate_output(test_name, actual_output, expected_output):
    if expected_output in actual_output:
        return "Pass"
    return f"Fail (Expected: {expected_output}, Got: {actual_output})"

# Main benchmarking loop
def main():
    # Prepare CSV file for results
    with open(OUTPUT_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Test Type', 'Base', 'Depth', 'Expression', 'Execution Time (s)', 'Output', 'Status', 'Validation Result'])

        print("Starting enhanced performance benchmarking for AoP calculations...")

# Part 1: Run predefined test cases for correctness
        print("Running predefined test cases for correctness validation...")
        for test_name, test_data in TEST_CASES.items():
            expression = test_data["expression"]
            base = test_data["base"]
            mode = test_data.get("mode", "num")
            expected_output = test_data["expected_output"]
            print(f"Testing {test_name}: {expression} with base={base}, mode={mode}")
            exec_time, output, status = run_command(expression, base, mode)
            validation_result = validate_output(test_name, output, expected_output) if status == 'Success' else "N/A (Test Failed)"
            writer.writerow([test_name, base, "N/A", expression, exec_time, output, status, validation_result])
            print(f"  Result: Average Time={exec_time:.4f}s over {ITERATIONS} iterations, Status={status}, Validation={validation_result}")

# Part 2: Run hyper-power benchmarks in AOP mode only with simpler expressions
        print("Running hyper-power performance benchmarks...")
        for base in BASES:
            for expression in EXPRESSIONS:
                # Test in AOP mode only
                print(f"Testing hyper-power (AOP): base={base}, expression={expression}")
                exec_time_aop, output_aop, status_aop = run_command(expression, base, mode="aop")
                writer.writerow(["hyper-power-aop", base, "N/A", expression, exec_time_aop, output_aop, status_aop, "N/A (Performance Test)"])
                print(f"  Result (AOP): Average Time={exec_time_aop:.4f}s over {ITERATIONS} iterations, Status={status_aop}")

    print(f"Benchmarking complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
