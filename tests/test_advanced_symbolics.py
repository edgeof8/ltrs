# tests/test_advanced_symbolics.py

import unittest
from src.aopl_python_impl.aop_calculator import AoPCalculator
from src.aopl_python_impl.definitions import OutputFormatMode

class TestAdvancedSymbolics(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10, output_mode=OutputFormatMode.AOP)

    def test_nested_powers(self):
        result = self.calculator.calculate("a^b^c")
        self.assertEqual(result, "a^e")

    def test_complex_symbolic_expression(self):
        result = self.calculator.calculate("(a^b + 1) - a^b")
        self.assertEqual(result, "0")

    def test_log_simplification(self):
        result = self.calculator.calculate("log(a^b)")
        self.assertEqual(result, "b")

if __name__ == '__main__':
    unittest.main()
