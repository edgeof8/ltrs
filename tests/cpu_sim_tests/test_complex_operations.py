import unittest
import random
import time
import sys
# Adjust path if necessary based on how tests are run and sys.path configuration
from aopl_python_impl.cpu_sim.hardware import CPU, power_integer, multiply_then_add

# Increase recursion limit for Karatsuba on large numbers
sys.setrecursionlimit(20000)

class TestComplexOperations(unittest.TestCase):

    def setUp(self):
        """Set up a CPU instance for the tests."""
        self.cpu = CPU()
        # Algorithms for general benchmarking
        self.BENCHMARK_ALGORITHMS = {
            "Schoolbook": self.cpu._multiply_schoolbook,
            "AoP_Optimized": self.cpu._multiply_aop_optimized,
            "Karatsuba": self.cpu._multiply_karatsuba,
            "Intelligent": self.cpu.intelligent_multiply,
        }
        # All algorithms for correctness tests
        self.ALL_ALGORITHMS_FOR_CORRECTNESS = {
            "Schoolbook": self.cpu._multiply_schoolbook,
            "AoP_Optimized": self.cpu._multiply_aop_optimized,
            "Karatsuba": self.cpu._multiply_karatsuba,
            "LookupTable": self.cpu._multiply_lookup_table, # Chunking LUT for correctness
            "Intelligent": self.cpu.intelligent_multiply,
        }
        self.COMPLEX_SCHOOLBOOK_CUTOFF_BITS = 64 # Skip Schoolbook for 64-bit and 128-bit complex ops

    COMPLEX_BIT_LENGTHS = [16, 32, 64, 128]
    POWER_EXPONENT = 5

    BIT_LENGTHS_TO_TEST = [32, 64, 128, 256, 512, 1024, 2048, 4096] # For power_calculation_benchmark

    def test_power_correctness(self): # Renamed for clarity
        """Verify power_integer produces correct results with all multiplication algorithms."""
        print("\n--- Running Power Correctness Suite (Complex Ops File) ---")
        test_cases = [(2, 10), (3, 5), (5, 3), (10, 2), (7, 0), (0, 5), (1, 100),
                      (random.randint(2,5), random.randint(2,4)), (random.randint(2,4), random.randint(5,7))]
        for base, exp in test_cases:
            ground_truth = base ** exp
            for algo_name, multiply_func in self.ALL_ALGORITHMS_FOR_CORRECTNESS.items():
                result = power_integer(base, exp, multiply_func)
                self.assertEqual(result, ground_truth,
                                 f"power_integer with {algo_name} failed for {base}^{exp}. Got {result}, expected {ground_truth}")
        print("power_integer passed correctness tests with all multiplication algorithms.")

    def test_multiply_add_correctness(self): # Renamed for clarity
        """Verify multiply_then_add produces correct results with all multiplication algorithms."""
        print("\n--- Running Multiply-Add Correctness Suite (Complex Ops File) ---")
        test_cases = [(2, 3, 4), (5, 0, 7), (0, 5, 7), (10, 10, 10), (1, 1, 1),
                      (random.randint(0,100), random.randint(0,100), random.randint(0,100)),
                      (random.randint(0,50), random.randint(0,50), random.randint(0,50))]
        for n1, n2, n3 in test_cases:
            ground_truth = (n1 * n2) + n3
            for algo_name, multiply_func in self.ALL_ALGORITHMS_FOR_CORRECTNESS.items():
                result = multiply_then_add(n1, n2, n3, multiply_func)
                self.assertEqual(result, ground_truth,
                                 f"multiply_then_add with {algo_name} failed for ({n1}*{n2})+{n3}. Got {result}, expected {ground_truth}")
        print("multiply_then_add passed correctness tests with all multiplication algorithms.")

    def test_complex_operations_performance(self):
        """Benchmark complex operations using different multiplication algorithms."""
        print("\n--- Running Complex Operations Performance Suite ---")
        tasks_to_benchmark = [
            ("Power", power_integer),
            ("Multiply-Add", multiply_then_add)
        ]
        print("Number of runs for complex operations will vary by bit length (see 'Runs' column). Some algos may be skipped.")

        header_algo_names = list(self.BENCHMARK_ALGORITHMS.keys())
        base_header_parts = [f"{'Operation':<15}", f"{'Input Bits':<10}", f"{'Runs':<5}", f"{'Exponent/N3 Bits':<18}"]
        algo_header_parts = [f"{name + ' Avg (s)':<18}" for name in header_algo_names]
        full_header = " | ".join(base_header_parts + algo_header_parts)
        print(full_header)
        print("-" * len(full_header))

        for task_display_name, operation_func in tasks_to_benchmark:
            for bits in self.COMPLEX_BIT_LENGTHS:
                runs_for_this_complex_op = 10
                if bits == 128:
                    runs_for_this_complex_op = 5

                base_n_power = random.randint(1 << (bits -1), (1 << bits) -1) if bits > 0 else random.randint(0,1)
                n1_ma = random.randint(1 << (bits -1), (1 << bits) -1) if bits > 0 else random.randint(0,1)
                n2_ma = random.randint(1 << (bits -1), (1 << bits) -1) if bits > 0 else random.randint(0,1)
                n3_ma = random.randint(1 << (bits -1), (1 << bits) -1) if bits > 0 else random.randint(0,1)

                row_output_parts = [f"{task_display_name:<15}", f"{bits:<10}", f"{runs_for_this_complex_op:<5}"]
                if task_display_name == "Power":
                    row_output_parts.append(f"{self.POWER_EXPONENT:<18}")
                elif task_display_name == "Multiply-Add":
                     row_output_parts.append(f"{bits:<18}")

                current_row_complex_avg_times = {name: "N/A" for name in header_algo_names}

                for algo_name, multiply_func in self.BENCHMARK_ALGORITHMS.items():
                    if algo_name == "Schoolbook" and bits >= self.COMPLEX_SCHOOLBOOK_CUTOFF_BITS:
                         current_row_complex_avg_times[algo_name] = "skipped"
                         continue

                    total_duration = 0
                    if runs_for_this_complex_op == 0:
                        avg_duration_val = 0.0
                    else:
                        # Warm-up
                        if operation_func == power_integer:
                            power_integer(base_n_power, self.POWER_EXPONENT, multiply_func)
                        elif operation_func == multiply_then_add:
                            multiply_then_add(n1_ma, n2_ma, n3_ma, multiply_func)

                        for _ in range(runs_for_this_complex_op):
                            start_time = time.perf_counter()
                            if operation_func == power_integer:
                                power_integer(base_n_power, self.POWER_EXPONENT, multiply_func)
                            elif operation_func == multiply_then_add:
                                multiply_then_add(n1_ma, n2_ma, n3_ma, multiply_func)
                            duration = time.perf_counter() - start_time
                            total_duration += duration
                        avg_duration_val = total_duration / runs_for_this_complex_op
                        current_row_complex_avg_times[algo_name] = f"{avg_duration_val:<18.6f}" if isinstance(avg_duration_val, float) else str(avg_duration_val)

                for algo_name_in_header in header_algo_names:
                    row_output_parts.append(f"{current_row_complex_avg_times[algo_name_in_header]:<18}")
                print(" | ".join(row_output_parts))
            print("-" * len(full_header))
        print("\n--- Complex Operations Performance Suite Complete ---")

    def test_power_calculation_benchmark(self):
        """Benchmarks power_integer with different CPU multiplication methods."""
        print("\n--- Power Calculation Benchmark (Base^Exponent) ---")
        test_cases = [
            ("2^1000", 2, 1000),
            ("3^630", 3, 630),
            ("17^250", 17, 250),
            ("2^2048", 2, 2048)
        ]
        num_runs = 3

        header_algo_names = list(self.BENCHMARK_ALGORITHMS.keys())
        header_parts = [f"{'Test Case':<12}", f"{'Runs':<5}"] + [f"{name + ' Avg (s)':<18}" for name in header_algo_names]
        header = " | ".join(header_parts)
        print(header)
        print("-" * len(header))

        for case_name, base, exponent in test_cases:
            row_output_parts = [f"{case_name:<12}", f"{num_runs:<5}"]
            current_row_avg_times = {name: "N/A" for name in header_algo_names}

            for algo_name, multiply_func in self.BENCHMARK_ALGORITHMS.items():
                if algo_name == "Schoolbook" and exponent >= 1000:
                    current_row_avg_times[algo_name] = "skipped"
                    continue

                total_duration = 0
                try:
                    power_integer(base, exponent, multiply_func) # Warm-up
                    for _ in range(num_runs):
                        start_time = time.perf_counter()
                        power_integer(base, exponent, multiply_func)
                        duration = time.perf_counter() - start_time
                        total_duration += duration
                    avg_duration = total_duration / num_runs
                    current_row_avg_times[algo_name] = f"{avg_duration:<18.6f}"
                except Exception as e:
                    print(f"Error during {algo_name} for {case_name}: {e}")
                    current_row_avg_times[algo_name] = "ERROR"

            for algo_name_in_header in header_algo_names:
                row_output_parts.append(f"{current_row_avg_times.get(algo_name_in_header, 'N/A'):<18}")
            print(" | ".join(row_output_parts))
        print("-" * len(header))
        print("--- Power Calculation Benchmark Complete ---")

if __name__ == '__main__':
    unittest.main()
