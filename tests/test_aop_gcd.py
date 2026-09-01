# tests/test_aop_gcd.py

import math
import os
import tempfile
import unittest

from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.aop_value import AoPValue
from src.aopl_python_impl.definitions import AoPError


class TestAoPGcd(unittest.TestCase):
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

    def test_infix_matches_python(self):
        self.assertEqual(self.ev("48 gcd 18"), "6")
        self.assertEqual(self.ev("0 gcd 18"), "18")
        self.assertEqual(self.ev("18 gcd 0"), "18")

    def test_letter_powers(self):
        self.assertEqual(self.ev("c gcd a", mode="aop"), "a")
        self.assertEqual(self.ev("Z gcd Y", mode="aop"), "Y")

    def test_method_matches_math_gcd(self):
        left = AoPValue.from_number(252, 10)
        right = AoPValue.from_number(105, 10)
        self.assertEqual(left.gcd(right).to_numerical(), math.gcd(252, 105))

    def test_huge_exponent_does_not_need_full_expand(self):
        huge = AoPValue(poly={str(2**40): 1}, base=10)
        with self.assertRaises(AoPError):
            huge.to_numerical()
        g = huge.gcd(AoPValue.from_number(25, 10))
        self.assertEqual(g.to_numerical(), 25)

    def test_huge_common_power_of_the_base(self):
        k = 2**40
        left = AoPValue(poly={str(k): 1}, base=10)
        right = AoPValue(poly={str(k - 1): 1}, base=10)
        g = left.gcd(right)
        self.assertEqual(g._rust_obj.get_poly(), {str(k - 1): 1})

    def test_mixed_bases_raise(self):
        left = AoPValue.from_number(10, 10)
        right = AoPValue.from_number(10, 2)
        with self.assertRaises(AoPError):
            left.gcd(right)
