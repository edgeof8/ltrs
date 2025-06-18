# tests/test_aop_calculator.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator # Renamed import
# Removed OutputFormatMode import as it's no longer used in AoP_Calculator

class TestAoPCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10) # Removed output_mode parameter

    def test_basic_addition(self):
        result = self.calculator.evaluate_expression("a + b") # Changed calculate to evaluate_expression
        self.assertEqual(result, "110") # a+b = 10+100 = 110

    def test_basic_multiplication(self):
        result = self.calculator.evaluate_expression("a * b") # Changed calculate to evaluate_expression
        self.assertEqual(result, "c") # a*b = 10^1 * 10^2 = 10^3 = c

    def test_power_operation(self):
        result = self.calculator.evaluate_expression("a ^ b") # Changed calculate to evaluate_expression
        self.assertEqual(result, "a^100") # (10^1)^(10^2) = 10^100

    def test_complex_expression(self):
        result = self.calculator.evaluate_expression("(a + b) * c") # Changed calculate to evaluate_expression
        self.assertEqual(result, "110*c") # (10+100)*10^3 = 110 * 10^3 = 110c

if __name__ == '__main__':
    unittest.main()
