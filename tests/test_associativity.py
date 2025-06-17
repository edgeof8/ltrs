# tests/test_associativity.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator # Renamed import
from src.aopl_python_impl.definitions import OutputFormatMode

class TestAssociativity(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10) # Removed output_mode parameter
        self.calculator.output_format_mode = OutputFormatMode.AOP # Set output_format_mode attribute

    def test_power_associativity(self):
        result = self.calculator.evaluate_expression("a^b^c") # Changed calculate to evaluate_expression
        self.assertEqual(result, "a^(a^2000)") # a^(b^c) = a^(10^2000)

    def test_multiplication_associativity(self):
        result = self.calculator.evaluate_expression("a * b * c") # Changed calculate to evaluate_expression
        self.assertEqual(result, "f") # a*b*c = 10^1*10^2*10^3 = 10^6 = f

if __name__ == '__main__':
    unittest.main()
