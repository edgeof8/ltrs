# tests/test_associativity.py

import unittest
from src.aopl_python_impl.aop_calculator import AoPCalculator
from src.aopl_python_impl.definitions import OutputFormatMode

class TestAssociativity(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10, output_mode=OutputFormatMode.AOP)

    def test_power_associativity(self):
        result = self.calculator.calculate("a^b^c")
        self.assertEqual(result, "a^e")

    def test_multiplication_associativity(self):
        result = self.calculator.calculate("a * b * c")
        self.assertEqual(result, "a^6")

if __name__ == '__main__':
    unittest.main()
