"""Computational certificates for docs/papers/letter-algebra.md.

Layer I: identities in Z[X] (hold in every base).
Layer II: same integer, possibly different AoP presentations.
Layer III: named equalities that hold only at a particular base.

`==` is structural equality of the pair (leading coefficient, sparse poly).
Factored form `1024 * (t)` and carried form `w + 2*u + 4*t` are the same
integer and currently compare unequal. Layer II therefore certifies with
matching **num** strings, and records the two aop presentations.
"""

import os
import tempfile
import unittest

from src.aopl_python_impl.aop_calculator import AoP_Calculator


class PaperIdentityMixin:
    def ev(self, expression, mode="num"):
        result, _ = self.calc.evaluate_expression(expression, mode=mode)
        return result

    def assertCertified(self, expression):
        self.assertEqual(self.ev(expression, mode="num"), "1", expression)


class TestLayerIFormal(PaperIdentityMixin, unittest.TestCase):
    """Theorems 1–3: juxtaposition, rank addition, translation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calc = AoP_Calculator(
            base=10, cache_file=os.path.join(self.tmp.name, "cache.json")
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_theorem_1_juxtaposition_is_addition(self):
        self.assertCertified("cQ == Q + c")
        self.assertCertified("ba == b + a")

    def test_theorem_2_letter_multiplication_adds_ranks(self):
        self.assertCertified("a * b == c")
        self.assertCertified("e * Q == V")
        self.assertCertified("e * c == h")

    def test_theorem_3_translation(self):
        self.assertCertified("cQ * e == V + h")
        self.assertEqual(self.ev("cQ * 2e", mode="aop"), "2 * (V + h)")
        self.assertEqual(self.ev("cQ * 2e"), self.ev("2 * (V + h)"))

    def test_layer_i_survives_base_change(self):
        other = tempfile.TemporaryDirectory()
        try:
            calc2 = AoP_Calculator(
                base=2, cache_file=os.path.join(other.name, "cache.json")
            )
            for expr in (
                "cQ == Q + c",
                "a * b == c",
                "cQ * e == V + h",
            ):
                result, _ = calc2.evaluate_expression(expr, mode="num")
                self.assertEqual(result, "1", f"base 2: {expr}")
        finally:
            other.cleanup()


class TestLayerIICovariant(PaperIdentityMixin, unittest.TestCase):
    """Theorem 5: coefficient-power. Same integer, two presentations."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calc = AoP_Calculator(
            base=10, cache_file=os.path.join(self.tmp.name, "cache.json")
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_theorem_5_num_strings_agree(self):
        left = self.ev("(2b)^a")
        right = self.ev("2^a * (b^a)")
        named = self.ev("1024 * t")
        self.assertEqual(left, "1024,00000,00000,00000,00000")
        self.assertEqual(left, right)
        self.assertEqual(left, named)

    def test_theorem_5_two_aop_presentations(self):
        factored = self.ev("(2b)^a", mode="aop")
        carried = self.ev("2^a * (b^a)", mode="aop")
        self.assertEqual(factored, "1024 * (t)")
        self.assertEqual(carried, "w + 2*u + 4*t")
        self.assertNotEqual(factored, carried)

    def test_theorem_5_structural_eq_does_not_see_the_integer(self):
        self.assertEqual(self.ev("(2b)^a == 2^a * (b^a)"), "0")
        self.assertEqual(self.ev("2b^a == 1024 * t"), "0")

    def test_theorem_5_num_strings_agree_at_base_2(self):
        other = tempfile.TemporaryDirectory()
        try:
            calc2 = AoP_Calculator(
                base=2, cache_file=os.path.join(other.name, "cache.json")
            )
            left, _ = calc2.evaluate_expression("(2b)^a", mode="num")
            right, _ = calc2.evaluate_expression("2^a * (b^a)", mode="num")
            self.assertEqual(left, right)
        finally:
            other.cleanup()


class TestLayerIIINamedAtBaseTen(PaperIdentityMixin, unittest.TestCase):
    """Theorem 6: naming that uses the base-10 rank map."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calc = AoP_Calculator(
            base=10, cache_file=os.path.join(self.tmp.name, "cache.json")
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_named_powers_at_base_10(self):
        self.assertCertified("b^a == t")
        self.assertCertified("b^2a == O")

    def test_factored_aop_names_the_coefficient(self):
        self.assertEqual(self.ev("2b^a", mode="aop"), "1024 * (t)")
        self.assertEqual(self.ev("2b^2a", mode="aop"), "1048576 * (O)")

    def test_support_gap_visible_in_num_mode(self):
        self.assertEqual(
            self.ev("Q + c"),
            "100,00000,00000,00000,00000,00000,00000,00000,01000",
        )
        self.assertEqual(
            self.ev("cQ * e"),
            "100,00000,00000,00000,00000,00000,00000,00000,01000,00000",
        )

    def test_named_powers_fail_at_base_2(self):
        other = tempfile.TemporaryDirectory()
        try:
            calc2 = AoP_Calculator(
                base=2, cache_file=os.path.join(other.name, "cache.json")
            )
            result, _ = calc2.evaluate_expression("b^a == t", mode="num")
            self.assertEqual(result, "0")
        finally:
            other.cleanup()
