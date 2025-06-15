import unittest
import random
import sys
from unittest import mock
# Adjust path if necessary based on how tests are run and sys.path configuration
from aopl_python_impl.cpu_sim.hardware import CPU

# Increase recursion limit for Karatsuba on large numbers
sys.setrecursionlimit(20000)

class TestIntelligentDispatcher(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU()
        self.schoolbook_path = 'aopl_python_impl.cpu_sim.hardware.CPU._multiply_schoolbook'
        self.aop_path = 'aopl_python_impl.cpu_sim.hardware.CPU._multiply_aop_optimized'
        self.karatsuba_path = 'aopl_python_impl.cpu_sim.hardware.CPU._multiply_karatsuba'
        self.lut_method_path = 'aopl_python_impl.cpu_sim.hardware.CPU._multiply_lookup_table'

    def test_intelligent_multiply_correctness(self):
        print("\n--- Running Intelligent Multiplier Correctness Suite (Dispatcher File) ---")
        test_cases = [
            (0, 0), (0, 123), (123, 0), (1, 1), (1, 123), (123, 1),
            (5, 7), (10, 20), (123, 456), (200, 250),
            ((1 << 30) -1, (1 << 20) -1),
            (1 << 64, (1 << 128) -1)
        ]
        for n1, n2 in test_cases:
            expected_result = n1 * n2
            result = self.cpu.intelligent_multiply(n1, n2)
            self.assertEqual(result, expected_result,
                             f"intelligent_multiply({n1}, {n2}) failed. Got {result}, expected {expected_result}")
        print("Intelligent multiplier passed basic correctness tests.")

    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_karatsuba')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_aop_optimized')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_schoolbook')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_lookup_table')
    def test_dispatcher_chooses_karatsuba(self, mock_lut_chunking, mock_schoolbook, mock_aop, mock_karatsuba):
        print("\n--- Verifying Karatsuba Dispatch ---")
        n1 = (1 << (self.cpu.KARATSUBA_THRESHOLD_BITS + 100)) - 123
        n2 = (1 << (self.cpu.KARATSUBA_THRESHOLD_BITS + 50)) - 456
        self.cpu.intelligent_multiply(n1, n2)
        mock_karatsuba.assert_called_once_with(n1, n2)
        mock_schoolbook.assert_not_called()
        mock_aop.assert_not_called()
        mock_lut_chunking.assert_not_called()
        print("Karatsuba dispatch verified.")

    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_karatsuba')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_aop_optimized')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_schoolbook')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_lookup_table')
    def test_dispatcher_chooses_schoolbook(self, mock_lut_chunking, mock_schoolbook, mock_aop, mock_karatsuba):
        print("\n--- Verifying Schoolbook Dispatch (Dense*Sparse) ---")
        dense_n = (1 << 128) - 1
        sparse_n = 1 << 64
        original_threshold = self.cpu.KARATSUBA_THRESHOLD_BITS
        # Temporarily lower threshold to ensure this specific case is tested against Schoolbook rule, not Karatsuba size rule
        self.cpu.KARATSUBA_THRESHOLD_BITS = max(256, dense_n.bit_length() + 10, sparse_n.bit_length() + 10)

        self.cpu.intelligent_multiply(dense_n, sparse_n)
        mock_schoolbook.assert_called_once_with(dense_n, sparse_n)
        mock_aop.assert_not_called()
        mock_karatsuba.assert_not_called()
        mock_lut_chunking.assert_not_called()

        self.cpu.KARATSUBA_THRESHOLD_BITS = original_threshold # Restore
        print("Schoolbook dispatch for dense*sparse verified.")

    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_karatsuba')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_aop_optimized')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_schoolbook')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_lookup_table')
    def test_dispatcher_chooses_aop_for_sparse_sparse(self, mock_lut_chunking, mock_schoolbook, mock_aop, mock_karatsuba):
        print("\n--- Verifying AoP Dispatch (Sparse*Sparse) ---")
        sparse_n1 = 1 << 60
        sparse_n2 = 1 << 70
        original_threshold = self.cpu.KARATSUBA_THRESHOLD_BITS
        # Temporarily lower threshold
        self.cpu.KARATSUBA_THRESHOLD_BITS = max(256, sparse_n1.bit_length() + 10, sparse_n2.bit_length() + 10)

        self.cpu.intelligent_multiply(sparse_n1, sparse_n2)
        mock_aop.assert_called_once_with(sparse_n1, sparse_n2)
        mock_schoolbook.assert_not_called()
        mock_karatsuba.assert_not_called()
        mock_lut_chunking.assert_not_called()

        self.cpu.KARATSUBA_THRESHOLD_BITS = original_threshold # Restore
        print("AoP dispatch for sparse*sparse verified.")

    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_karatsuba')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_aop_optimized')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_schoolbook')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_lookup_table')
    def test_dispatcher_chooses_aop_for_default(self, mock_lut_chunking, mock_schoolbook, mock_aop, mock_karatsuba):
        print("\n--- Verifying AoP Dispatch (Default Case) ---")
        n1 = random.randint(1 << 500, (1 << 512) - 1)
        n2 = random.randint(1 << 500, (1 << 512) - 1)

        original_karatsuba_threshold = self.cpu.KARATSUBA_THRESHOLD_BITS
        self.cpu.KARATSUBA_THRESHOLD_BITS = 1024 # Ensure default threshold for this test

        self.cpu.intelligent_multiply(n1, n2)
        mock_aop.assert_called_once_with(n1, n2)
        mock_schoolbook.assert_not_called()
        mock_karatsuba.assert_not_called()
        mock_lut_chunking.assert_not_called()

        self.cpu.KARATSUBA_THRESHOLD_BITS = original_karatsuba_threshold # Restore
        print("AoP dispatch for default case verified.")

    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_karatsuba')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_aop_optimized')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_schoolbook')
    @mock.patch('aopl_python_impl.cpu_sim.hardware.CPU._multiply_lookup_table')
    def test_dispatcher_chooses_direct_lut(self, mock_lut_method, mock_schoolbook, mock_aop, mock_karatsuba):
        print("\n--- Verifying Direct LUT Dispatch ---")
        n1 = 10
        n2 = 15
        result = self.cpu.intelligent_multiply(n1, n2)
        self.assertEqual(result, n1 * n2)

        mock_lut_method.assert_not_called()
        mock_schoolbook.assert_not_called()
        mock_aop.assert_not_called()
        mock_karatsuba.assert_not_called()
        print("Direct LUT dispatch (by not calling other methods) verified.")

if __name__ == '__main__':
    unittest.main()
