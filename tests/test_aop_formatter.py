# tests/test_aop_formatter.py

import unittest
from src.aopl_python_impl.aop_formatter import format_output, represent_exponent_as_aop_term
from src.aopl_python_impl.definitions import ValueTuple, OutputFormatMode

class TestAoPFormatter(unittest.TestCase):
    def setUp(self):
        self.base = 10
        self.get_letter_func = lambda x: "abcdefghijklmnopqrstuvwxyz"[x-1] if 1 <= x <= 26 else ""
        self.represent_exponent_func = represent_exponent_as_aop_term
        self.normalize_func = lambda x: x
        self.precision = 6

    def test_simple_values(self):
        self.assertEqual(format_output((1.0, 0), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "1")
        self.assertEqual(format_output((0.0, 0), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "0")
        self.assertEqual(format_output((-1.0, 0), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "-1")

    def test_letter_representation(self):
        self.assertEqual(format_output((1.0, 1), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "a")
        self.assertEqual(format_output((1.0, 2), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "b")
        self.assertEqual(format_output((1.0, 26), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "z")

    def test_large_exponents(self):
        self.assertEqual(format_output((1.0, 27), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "a^27")
        self.assertEqual(format_output((1.0, 100), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "a^100")

    def test_coefficient_with_exponent(self):
        self.assertEqual(format_output((2.0, 1), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "2 * a")
        self.assertEqual(format_output((-2.0, 2), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.AOP, self.normalize_func, self.precision), "-2 * b")

    def test_numerical_output(self):
        self.assertEqual(format_output((1.0, 1), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.NUMERICAL, self.normalize_func, self.precision), "10")
        self.assertEqual(format_output((2.0, 1), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.NUMERICAL, self.normalize_func, self.precision), "20")

    def test_scientific_output(self):
        self.assertEqual(format_output((1.0, 2), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.SCIENTIFIC, self.normalize_func, self.precision), "1 * 10^2")
        self.assertEqual(format_output((2.0, 3), self.base, self.get_letter_func, self.represent_exponent_func, OutputFormatMode.SCIENTIFIC, self.normalize_func, self.precision), "2 * 10^3")

    def test_represent_exponent_as_aop_term(self):
        self.assertEqual(represent_exponent_as_aop_term(1, self.base, self.get_letter_func), "a")
        self.assertEqual(represent_exponent_as_aop_term(26, self.base, self.get_letter_func), "z")
        self.assertEqual(represent_exponent_as_aop_term(27, self.base, self.get_letter_func), "27")
        self.assertEqual(represent_exponent_as_aop_term(100, self.base, self.get_letter_func), "100")
        self.assertEqual(represent_exponent_as_aop_term(1000, self.base, self.get_letter_func), "1000")

if __name__ == '__main__':
    unittest.main()
