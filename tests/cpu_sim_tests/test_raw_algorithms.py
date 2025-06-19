import unittest
import random
import time
import sys
# Assuming hardware.py is in src.aopl_python_impl.cpu_sim
# Adjust path if necessary based on how tests are run and sys.path configuration
from aopl_python_impl.cpu_sim.hardware import CPU

# Increase recursion limit for Karatsuba on large numbers
sys.setrecursionlimit(20000)

class TestRawMultiplicationAlgorithms(unittest.TestCase):

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
        # Cutoff for skipping Schoolbook in general suite if it becomes too slow
        self.SCHOOLBOOK_BENCHMARK_CUTOFF_BITS = 256

    BIT_LENGTHS_TO_TEST = [32, 64, 128, 256, 512, 1024, 2048, 4096]

    def test_correctness_raw_algorithms(self): # Renamed for clarity
        """Verify all raw multiplication algorithms produce correct results."""
        print("\n--- Running Raw Algorithms Correctness Suite ---")
        for name, func in self.ALL_ALGORITHMS_FOR_CORRECTNESS.items():
            print(f"Verifying {name} algorithm...")
            test_cases = [(0,0), (0,123), (123,0), (1,1), (1,123), (123,1)]
            for _ in range(20):
                test_cases.append((random.randint(0, 1000), random.randint(0, 1000)))
            test_cases.append((random.randint(1 << 15, (1 << 16) -1), random.randint(1 << 15, (1 << 16) -1)))
            for n1, n2 in test_cases:
                ground_truth = n1 * n2
                result = func(n1, n2)
                self.assertEqual(result, ground_truth,
                                 f"{name} failed for {n1} * {n2}. Got {result}, expected {ground_truth}")
        print("All raw algorithms passed correctness tests.")

    def test_performance_suite_raw_algorithms(self): # Renamed for clarity
        """Benchmark selected raw multiplication algorithms against each other."""
        print("\n--- Running Raw Algorithms Performance Suite ---")
        results = {name: [] for name in self.BENCHMARK_ALGORITHMS}
        print("Number of runs per bit length will vary (see 'Runs' column). Schoolbook may be skipped for larger sizes.")

        header_algo_names = list(self.BENCHMARK_ALGORITHMS.keys())
        header_parts = [f"{'Bit Length':<12}", f"{'Runs':<5}"] + [f"{name + ' Avg (s)':<18}" for name in header_algo_names]
        header = " | ".join(header_parts)
        print(header)
        print("-" * len(header))

        for bits in self.BIT_LENGTHS_TO_TEST:
            runs_for_this_bit_length = 0
            if bits <= 128:
                runs_for_this_bit_length = 50
            elif bits == 256:
                runs_for_this_bit_length = 25
            elif bits == 512:
                runs_for_this_bit_length = 15
            elif bits == 1024:
                runs_for_this_bit_length = 10
            elif bits == 2048:
                runs_for_this_bit_length = 5
            elif bits == 4096:
                runs_for_this_bit_length = 3
            else:
                runs_for_this_bit_length = 1

            n1 = random.randint(1 << (bits - 1), (1 << bits) - 1)
            n2 = random.randint(1 << (bits - 1), (1 << bits) - 1)
            current_row_avg_times = {name: "N/A" for name in header_algo_names}

            for name, func in self.BENCHMARK_ALGORITHMS.items():
                if name == "Schoolbook" and bits >= self.SCHOOLBOOK_BENCHMARK_CUTOFF_BITS:
                    results[name].append(float('inf'))
                    current_row_avg_times[name] = "skipped"
                    continue

                total_duration = 0
                if runs_for_this_bit_length == 0:
                    avg_duration = 0.0
                else:
                    func(n1, n2) # Warm-up
                    for _ in range(runs_for_this_bit_length):
                        start_time = time.perf_counter()
                        func(n1, n2)
                        duration = time.perf_counter() - start_time
                        total_duration += duration
                    avg_duration = total_duration / runs_for_this_bit_length

                results[name].append(avg_duration)
                current_row_avg_times[name] = f"{avg_duration:<18.6f}" if isinstance(avg_duration, float) else avg_duration

            row_output_parts = [f"{bits:<12}", f"{runs_for_this_bit_length:<5}"]
            for algo_name_in_header in header_algo_names:
                 row_output_parts.append(f"{current_row_avg_times.get(algo_name_in_header, 'N/A'):<18}")
            print(" | ".join(row_output_parts))

        print("\n--- Raw Algorithms Performance Suite Complete ---")
        if "Karatsuba" in results and "Schoolbook" in results:
            valid_indices = [
                i for i, (k, s) in enumerate(zip(results["Karatsuba"], results["Schoolbook"]))
                if isinstance(k, float) and isinstance(s, float) and k != float('inf') and s != float('inf')
            ]
            if valid_indices:
                last_schoolbook_run_idx = -1
                for i in range(len(self.BIT_LENGTHS_TO_TEST) -1, -1, -1):
                    if self.BIT_LENGTHS_TO_TEST[i] < self.SCHOOLBOOK_BENCHMARK_CUTOFF_BITS:
                        if i < len(results["Schoolbook"]) and isinstance(results["Schoolbook"][i], float) and results["Schoolbook"][i] != float('inf'):
                             last_schoolbook_run_idx = i
                             break

                if last_schoolbook_run_idx != -1 and \
                   last_schoolbook_run_idx < len(results["Karatsuba"]) and \
                   isinstance(results["Karatsuba"][last_schoolbook_run_idx], float) and \
                   results["Karatsuba"][last_schoolbook_run_idx] != float('inf'):

                    bits_at_comparison = self.BIT_LENGTHS_TO_TEST[last_schoolbook_run_idx]
                    if bits_at_comparison >= 128:
                        self.assertLess(results["Karatsuba"][last_schoolbook_run_idx], results["Schoolbook"][last_schoolbook_run_idx],
                                        f"Karatsuba ({results['Karatsuba'][last_schoolbook_run_idx]:.6f}s) was not faster than Schoolbook ({results['Schoolbook'][last_schoolbook_run_idx]:.6f}s) for {bits_at_comparison}-bit numbers.")

    def test_performance_schoolbook_wins(self): # Renamed slightly for consistency
        print("\n--- Running Performance Test: Schoolbook's Best Case (Raw) ---")
        n1 = (1 << 128) - 1
        s1_bits = n1.bit_length()
        n2 = 1 << 64
        print(f"Multiplying a DENSE number ({s1_bits} set bits) by a SPARSE number (1 set bit at 2^64).")
        print("Hypothesis: Schoolbook will be faster.")
        num_runs = 20
        total_time_schoolbook = 0
        total_time_aop = 0
        self.cpu._multiply_schoolbook(n1, n2)
        self.cpu._multiply_aop_optimized(n1, n2)
        for _ in range(num_runs):
            start_time = time.perf_counter()
            self.cpu._multiply_schoolbook(n1, n2)
            total_time_schoolbook += (time.perf_counter() - start_time)
            start_time = time.perf_counter()
            self.cpu._multiply_aop_optimized(n1, n2)
            total_time_aop += (time.perf_counter() - start_time)
        avg_time_schoolbook = total_time_schoolbook / num_runs
        avg_time_aop = total_time_aop / num_runs
        print(f"\nAverage Time (Schoolbook): {avg_time_schoolbook:.6f} seconds")
        print(f"Average Time (AoP):        {avg_time_aop:.6f} seconds")
        self.assertLess(avg_time_schoolbook, avg_time_aop, "Schoolbook method was not faster than AoP for the dense*sparse case.")
        if avg_time_schoolbook > 0 :
            speedup = avg_time_aop / avg_time_schoolbook
            print(f"Schoolbook was {speedup:.2f}x faster in this specific scenario.")
        else:
            print("Schoolbook execution time was too small to calculate speedup reliably.")

    def test_performance_aop_wins_sparse_x_sparse(self): # Renamed slightly
        print("\n--- Running Performance Test: AoP's Best Case (Sparse x Sparse - Raw) ---")
        n1_exp, n2_exp = 64, 65
        n1, n2 = 1 << n1_exp, 1 << n2_exp
        print(f"Multiplying two SPARSE numbers: 2^{n1_exp} * 2^{n2_exp}.")
        print("Hypothesis: AoP_Optimized will be the fastest.")
        num_runs = 50

        algos_to_compare = {
            "Schoolbook": self.cpu._multiply_schoolbook,
            "AoP_Optimized": self.cpu._multiply_aop_optimized,
            "Karatsuba": self.cpu._multiply_karatsuba,
            # Intelligent will pick AoP here, so including it is fine for comparison
            "Intelligent": self.cpu.intelligent_multiply
        }
        total_times = {name: 0.0 for name in algos_to_compare}

        for multiply_func in algos_to_compare.values():
            multiply_func(n1, n2)
        for _ in range(num_runs):
            for name, multiply_func in algos_to_compare.items():
                start_time = time.perf_counter()
                multiply_func(n1, n2)
                total_times[name] += (time.perf_counter() - start_time)
        avg_times = {name: total_time / num_runs for name, total_time in total_times.items()}
        print("\nAverage Times:")
        for name, avg_time in avg_times.items():
            print(f"  {name:<15}: {avg_time:.8f} seconds")
        self.assertLess(avg_times["AoP_Optimized"], avg_times["Schoolbook"], "AoP_Optimized was not faster than Schoolbook for sparse*sparse case.")
        self.assertLess(avg_times["AoP_Optimized"], avg_times["Karatsuba"], "AoP_Optimized was not faster than Karatsuba for sparse*sparse case.")
        if avg_times["AoP_Optimized"] > 0:
            if "Schoolbook" in avg_times:
                speedup_vs_schoolbook = avg_times["Schoolbook"] / avg_times["AoP_Optimized"]
                print(f"AoP_Optimized was {speedup_vs_schoolbook:.2f}x faster than Schoolbook.")
            if "Karatsuba" in avg_times:
                speedup_vs_karatsuba = avg_times["Karatsuba"] / avg_times["AoP_Optimized"]
                print(f"AoP_Optimized was {speedup_vs_karatsuba:.2f}x faster than Karatsuba.")
        else:
            print("AoP_Optimized execution time was too small to calculate speedup reliably.")

    def test_performance_karatsuba_wins_large_equal_size(self): # Renamed slightly
        print("\n--- Running Performance Test: Karatsuba's Best Case (Large Random x Large Random - Raw) ---")
        test_bits = 2048
        n1 = random.randint(1 << (test_bits - 1), (1 << test_bits) - 1)
        n2 = random.randint(1 << (test_bits - 1), (1 << test_bits) - 1)
        print(f"Multiplying two random {test_bits}-bit numbers.")
        print("Hypothesis: Karatsuba will be the fastest.")
        num_runs = 2
        algos_to_test_here = {
            "Schoolbook": self.cpu._multiply_schoolbook,
            "AoP_Optimized": self.cpu._multiply_aop_optimized,
            "Karatsuba": self.cpu._multiply_karatsuba,
        }
        total_times = {name: 0.0 for name in algos_to_test_here}
        for multiply_func in algos_to_test_here.values():
            multiply_func(n1, n2)
        for _ in range(num_runs):
            for name, multiply_func in algos_to_test_here.items():
                start_time = time.perf_counter()
                multiply_func(n1, n2)
                total_times[name] += (time.perf_counter() - start_time)
        avg_times = {name: total_time / num_runs for name, total_time in total_times.items()}
        print("\nAverage Times:")
        for name, avg_time in avg_times.items():
            print(f"  {name:<15}: {avg_time:.6f} seconds")
        self.assertLess(avg_times["Karatsuba"], avg_times["Schoolbook"],
                        f"Karatsuba was not faster than Schoolbook for {test_bits}-bit numbers.")
        self.assertLess(avg_times["Karatsuba"], avg_times["AoP_Optimized"],
                        f"Karatsuba was not faster than AoP_Optimized for {test_bits}-bit numbers.")
        if avg_times["Karatsuba"] > 0:
            speedup_vs_schoolbook = avg_times["Schoolbook"] / avg_times["Karatsuba"]
            speedup_vs_aop = avg_times["AoP_Optimized"] / avg_times["Karatsuba"]
            print(f"Karatsuba was {speedup_vs_schoolbook:.2f}x faster than Schoolbook for {test_bits}-bit numbers.")
            print(f"Karatsuba was {speedup_vs_aop:.2f}x faster than AoP_Optimized for {test_bits}-bit numbers.")
        else:
            print("Karatsuba execution time was too small to calculate speedup reliably.")

if __name__ == '__main__':
    unittest.main() # This will run tests in this file if executed directly
