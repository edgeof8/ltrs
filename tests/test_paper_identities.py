"""Computational certificates for docs/papers/letter-algebra.md.

Layer I: identities in Z[X] (hold in every base).
Layer II: same integer after evaluation at every base B >= 2.
Layer III: named equalities that hold only at a particular base.

`==` is canonical equality: distribute the leading coefficient, carry, compare
sparse digit maps. Factored `1024 * (t)` and carried `w + 2*u + 4*t` compare
equal. The aop printer may still show two presentations.
"""

import os
import tempfile
import unittest

from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.aop_value import AoPValue


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
        self.assertCertified("cQ * 2e == 2 * (V + h)")

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
                "cQ * 2e == 2 * (V + h)",
            ):
                result, _ = calc2.evaluate_expression(expr, mode="num")
                self.assertEqual(result, "1", f"base 2: {expr}")
        finally:
            other.cleanup()


class TestLayerIICovariant(PaperIdentityMixin, unittest.TestCase):
    """Theorem 5: coefficient-power. Canonical == sees through presentations."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calc = AoP_Calculator(
            base=10, cache_file=os.path.join(self.tmp.name, "cache.json")
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_theorem_5_canonical_eq(self):
        self.assertCertified("(2b)^a == 2^a * (b^a)")
        self.assertCertified("2b^a == 1024 * t")
        self.assertCertified("(2b)^2a == 2^(2a) * (b^2a)")
        self.assertCertified("2b^2a == 1048576 * O")

    def test_theorem_5_aop_keeps_two_presentations(self):
        factored = self.ev("(2b)^a", mode="aop")
        carried = self.ev("2^a * (b^a)", mode="aop")
        self.assertEqual(factored, "1024 * (t)")
        self.assertEqual(carried, "w + 2*u + 4*t")
        self.assertNotEqual(factored, carried)

    def test_theorem_5_canonical_eq_at_base_2(self):
        other = tempfile.TemporaryDirectory()
        try:
            calc2 = AoP_Calculator(
                base=2, cache_file=os.path.join(other.name, "cache.json")
            )
            result, _ = calc2.evaluate_expression(
                "(2b)^a == 2^a * (b^a)", mode="num"
            )
            self.assertEqual(result, "1")
            factored, _ = calc2.evaluate_expression("(2b)^a", mode="aop")
            carried, _ = calc2.evaluate_expression("2^a * (b^a)", mode="aop")
            self.assertEqual(factored, "4 * (d)")
            self.assertEqual(carried, "f")
        finally:
            other.cleanup()

    def test_theorem_5_canonical_eq_at_base_16(self):
        other = tempfile.TemporaryDirectory()
        try:
            calc16 = AoP_Calculator(
                base=16, cache_file=os.path.join(other.name, "cache.json")
            )
            result, _ = calc16.evaluate_expression(
                "(2b)^a == 2^a * (b^a)", mode="num"
            )
            self.assertEqual(result, "1")
            factored, _ = calc16.evaluate_expression("(2b)^a", mode="aop")
            carried, _ = calc16.evaluate_expression("2^a * (b^a)", mode="aop")
            self.assertEqual(factored, "65536 * (G)")
            self.assertEqual(carried, "K")
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
        self.assertCertified("2^a == 1024")

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
            result, _ = calc2.evaluate_expression("2^a == 1024", mode="num")
            self.assertEqual(result, "0")
            ba, _ = calc2.evaluate_expression("b^a", mode="aop")
            self.assertEqual(ba, "d")
        finally:
            other.cleanup()

    def test_named_powers_fail_at_base_16(self):
        other = tempfile.TemporaryDirectory()
        try:
            calc16 = AoP_Calculator(
                base=16, cache_file=os.path.join(other.name, "cache.json")
            )
            result, _ = calc16.evaluate_expression("b^a == t", mode="num")
            self.assertEqual(result, "0")
            result, _ = calc16.evaluate_expression("2^a == 1024", mode="num")
            self.assertEqual(result, "0")
            ba, _ = calc16.evaluate_expression("b^a", mode="aop")
            self.assertEqual(ba, "G")
            two_a, _ = calc16.evaluate_expression("2^a", mode="aop")
            self.assertEqual(two_a, "d")
        finally:
            other.cleanup()

    def test_layer_i_survives_base_16(self):
        other = tempfile.TemporaryDirectory()
        try:
            calc16 = AoP_Calculator(
                base=16, cache_file=os.path.join(other.name, "cache.json")
            )
            for expr in ("cQ * e == V + h", "a * b == c"):
                result, _ = calc16.evaluate_expression(expr, mode="num")
                self.assertEqual(result, "1", f"base 16: {expr}")
        finally:
            other.cleanup()


class TestCanonicalPresentation(unittest.TestCase):
    """Theorem 7: (k, p) ~ (k', p') iff carry(k p) = carry(k' p')."""

    def test_factored_monomial_equals_carried(self):
        factored = AoPValue(poly={"20": 1}, base=10, coeff=1024)
        carried = AoPValue.from_number(1024, 10) * AoPValue.from_literal("t", 10)
        self.assertEqual(factored, carried)
        self.assertEqual(
            factored.canonical_digits(),
            {20: 4, 21: 2, 23: 1},
        )
        self.assertEqual(factored.canonical_digits(), carried.canonical_digits())

    def test_mixed_bases_are_unequal(self):
        left = AoPValue.from_number(1, 10)
        right = AoPValue.from_number(1, 2)
        self.assertNotEqual(left, right)
