# tests/test_advanced_symbolics.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator # Renamed import
from src.aopl_python_impl.definitions import OutputFormatMode

class TestAdvancedSymbolics(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10) # Removed output_mode parameter
        self.calculator.output_format_mode = OutputFormatMode.AOP # Set output_format_mode attribute

    def test_nested_powers(self):
        result = self.calculator.evaluate_expression("a^b^c") # Changed calculate to evaluate_expression
        self.assertEqual(result, "a^(a^2000)") # a^(b^c) = a^(10^2000)

    def test_complex_symbolic_expression(self):
        # Test that adding 1 to an overflowing number correctly raises an error.
        # a^b is 10^100, which overflows numerical representation.
        result = self.calculator.evaluate_expression("a^b + 1")
        self.assertTrue("Error: Cannot add/subtract values of this magnitude." in result)

    def test_log_simplification(self):
        # log(a^b) = log((10^1)^(10^2)) = log(10^100) = 100.
        # Formatted as a^100 if 100 has no letter.
        result = self.calculator.evaluate_expression("log(a^b)") # Changed calculate to evaluate_expression
        self.assertEqual(result, "a^100")

if __name__ == '__main__':
    unittest.main()
