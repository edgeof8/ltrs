# tests/test_aop_language_spec.py
"""Executable language spec: juxtaposition, *, trailing =, exact /."""

import os
import tempfile
import unittest

from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.definitions import AoPError


class TestAoPLanguageSpec(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calc = AoP_Calculator(
            base=10, cache_file=os.path.join(self.tmp.name, "cache.json")
        )

    def tearDown(self):
        self.tmp.cleanup()

    def ev(self, expression, mode="num"):
        result, _ = self.calc.evaluate_expression(expression, mode=mode)
        return result

    def test_juxtaposition_adds_letters(self):
        self.assertEqual(self.ev("ba"), "110")
        self.assertEqual(self.ev("cab"), "1110")
        self.assertEqual(self.ev("2c4a"), "2040")

    def test_juxtaposition_is_not_multiplication(self):
        self.assertNotEqual(self.ev("ba"), self.ev("a * b"))
        self.assertEqual(self.ev("a * b"), "1000")

    def test_star_multiplies_and_aop_uses_letter_map(self):
        self.assertEqual(self.ev("a * b", mode="aop"), "c")
        self.assertEqual(self.ev("a * b * c", mode="aop"), "f")

    def test_power_letter_map(self):
        self.assertEqual(self.ev("a ^ b", mode="aop"), "Z")

    def test_trailing_equals_evaluates_lhs(self):
        self.assertEqual(self.ev("a="), self.ev("a"))
        self.assertEqual(self.ev("3e3 ="), self.ev("3e3"))

    def test_exact_division(self):
        self.assertEqual(self.ev("c / a"), "100")
        self.assertEqual(self.ev("(a + b) / a"), "11")
        self.assertEqual(self.ev("10 / 2"), "5")

    def test_inexact_and_zero_division_raise(self):
        with self.assertRaises(AoPError):
            self.ev("a / b")
        with self.assertRaises(AoPError):
            self.ev("a / 0")

    def test_equality_is_polynomial_identity(self):
        self.assertEqual(self.ev("a == 10"), "1")
        self.assertEqual(self.ev("a == b"), "0")
        self.assertEqual(self.ev("ba == (b + a)"), "1")
        self.assertEqual(self.ev("cQ == Q + c"), "1")
        self.assertEqual(self.ev("(2b)^a == 1024 * t"), "1")

    def test_base_change_reinterprets_letters_not_digits(self):
        ten = AoP_Calculator(base=10, cache_file=os.path.join(self.tmp.name, "b10.json"))
        two = AoP_Calculator(base=2, cache_file=os.path.join(self.tmp.name, "b2.json"))
        a_ten, _ = ten.evaluate_expression("a", mode="num")
        a_two, _ = two.evaluate_expression("a", mode="num")
        self.assertEqual(a_ten, "10")
        self.assertEqual(a_two, "2")

    def test_grouped_digits_round_trip(self):
        self.assertEqual(self.ev("1,00000"), "1,00000")
        self.assertEqual(self.ev("5,00000 + 2"), "5,00002")
        self.assertEqual(self.ev("1,00000"), self.ev("100000"))
