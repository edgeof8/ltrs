# tests/test_aop_calculator.py

import unittest
from src.aopl_python_impl.aop_calculator import AoPCalculator
from src.aopl_python_impl.definitions import OutputFormatMode

class TestAoPCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10, output_mode=OutputFormatMode.AOP)

    def test_basic_addition(self):
        result = self.calculator.calculate("a + b")
        self.assertEqual(result, "1.1 * a^2")

    def test_basic_multiplication(self):
        result = self.calculator.calculate("a * b")
        self.assertEqual(result, "a^3")

    def test_power_operation(self):
        result = self.calculator.calculate("a ^ b")
        self.assertEqual(result, "a^100")

    def test_complex_expression(self):
        result = self.calculator.calculate("(a + b) * c")
        self.assertEqual(result, "1.1 * a^4")

if __name__ == '__main__':
    unittest.main()
