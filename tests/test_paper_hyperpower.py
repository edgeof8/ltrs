"""Certificates for docs/papers/hyperpower-collapse.md.

Hyperpowers stay sparse monomials. Compare with == in aop mode; do not
evaluate Z^e in num mode.
"""

import os
import tempfile
import unittest

from src.aopl_python_impl.aop_calculator import AoP_Calculator


class HyperpowerMixin:
    def ev(self, expression, mode="aop"):
        result, _ = self.calc.evaluate_expression(expression, mode=mode)
        return result

    def assertCertified(self, expression):
        self.assertEqual(self.ev(expression), "1", expression)


class TestCollapseAtBaseTen(HyperpowerMixin, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calc = AoP_Calculator(
            base=10, cache_file=os.path.join(self.tmp.name, "cache.json")
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_theorem_2_named_collapse_chain(self):
        self.assertEqual(self.ev("Z^a"), "a^c")
        self.assertEqual(self.ev("Z^b"), "a^d")
        self.assertEqual(self.ev("Z^c"), "a^e")
        self.assertEqual(self.ev("Z^d"), "a^f")
        self.assertEqual(self.ev("Z^e"), "a^g")
        self.assertCertified("Z^a == a^c")
        self.assertCertified("Z^b == a^d")
        self.assertCertified("Z^c == a^e")
        self.assertCertified("Z^d == a^f")
        self.assertCertified("Z^e == a^g")

    def test_y_is_not_a_pure_power_of_the_base(self):
        self.assertEqual(self.ev("Y^e"), "a^(5*f)")
        self.assertCertified("Y^e == a^(5*f)")
        self.assertEqual(self.ev("Y^e == a^f"), "0")

    def test_theorem_3_inverse_name(self):
        self.assertCertified("a^b == Z")

    def test_theorem_4_tower(self):
        self.assertEqual(self.ev("a^b^c"), "a^(a^(2*c))")
        self.assertCertified("a^b^c == a^(a^(2*c))")
        self.assertEqual(self.ev("Z^Z"), "a^(a^(b + 2))")
        self.assertCertified("Z^Z == a^(a^(b + 2))")

    def test_theorem_5_product_base_not_juxtaposition(self):
        self.assertEqual(self.ev("(d*o*g)^c"), "a^(2*d + 6*c)")
        self.assertCertified("(d*o*g)^c == a^(2*d + 6*c)")
        self.assertEqual(self.ev("(a*Z)^b"), "a^(d + b)")
        self.assertCertified("(a*Z)^b == a^(d + b)")


class TestCollapseBaseChange(unittest.TestCase):
    def _calc(self, base):
        tmp = tempfile.TemporaryDirectory()
        calc = AoP_Calculator(
            base=base, cache_file=os.path.join(tmp.name, "cache.json")
        )
        return calc, tmp

    def test_named_collapse_fails_at_base_2(self):
        calc, tmp = self._calc(2)
        try:
            z_e, _ = calc.evaluate_expression("Z^e", mode="aop")
            self.assertEqual(z_e, "a^(k + j + g)")
            eq, _ = calc.evaluate_expression("Z^e == a^g", mode="aop")
            self.assertEqual(eq, "0")
            ab, _ = calc.evaluate_expression("a^b", mode="aop")
            self.assertEqual(ab, "d")
            eq, _ = calc.evaluate_expression("a^b == Z", mode="aop")
            self.assertEqual(eq, "0")
        finally:
            tmp.cleanup()

    def test_named_collapse_fails_at_base_16(self):
        calc, tmp = self._calc(16)
        try:
            z_e, _ = calc.evaluate_expression("Z^e", mode="aop")
            self.assertEqual(z_e, "a^(6*f + 4*e)")
            eq, _ = calc.evaluate_expression("Z^e == a^g", mode="aop")
            self.assertEqual(eq, "0")
            eq, _ = calc.evaluate_expression("a^b == Z", mode="aop")
            self.assertEqual(eq, "0")
        finally:
            tmp.cleanup()

    def test_reflexive_survives(self):
        for base in (2, 10, 16):
            calc, tmp = self._calc(base)
            try:
                eq, _ = calc.evaluate_expression("Z^e == Z^e", mode="aop")
                self.assertEqual(eq, "1", f"base {base}")
            finally:
                tmp.cleanup()
