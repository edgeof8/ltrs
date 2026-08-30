# tests/test_aop_formatter.py

import unittest
from src.aopl_python_impl.aop_formatter import format_as_aop, format_as_decimal_string
from src.aopl_python_impl.aop_value import AoPValue


class TestAoPFormatter(unittest.TestCase):
    def test_simple_values(self):
        self.assertEqual(format_as_aop(AoPValue.from_number(1)), "1")
        self.assertEqual(format_as_aop(AoPValue.from_number(0)), "0")
        self.assertEqual(format_as_aop(AoPValue.from_number(-1)), "-1")

    def test_letter_decimal_values(self):
        self.assertEqual(format_as_decimal_string(AoPValue.from_literal("a")), "10")
        self.assertEqual(format_as_decimal_string(AoPValue.from_literal("b")), "100")
        self.assertEqual(format_as_decimal_string(AoPValue.from_literal("2a")), "20")

    def test_coefficient_aop_form(self):
        self.assertEqual(format_as_aop(AoPValue.from_literal("2a")), "2 * (a)")

    def test_additive_literal(self):
        self.assertEqual(format_as_decimal_string(AoPValue.from_literal("ba")), "110")
        self.assertEqual(format_as_aop(AoPValue.from_literal("a")), "a^1")
