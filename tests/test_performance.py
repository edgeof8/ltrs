# tests/test_performance.py

import unittest
import time
from src.aopl_python_impl.aop_calculator import AoPCalculator
from src.aopl_python_impl.definitions import OutputFormatMode

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10, output_mode=OutputFormatMode.AOP)

    def test_large_power_tower(self):
        start_time = time.time()
        result = self.calculator.calculate("a^b^c^d^e^f^g^h")
        end_time = time.time()
        self.assertEqual(result, "a^iz")
        self.assertLess(end_time - start_time, 1.0, "Performance test failed: took too long")

if __name__ == '__main__':
    unittest.main()
