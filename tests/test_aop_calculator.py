# tests/test_aop_calculator.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator
from src.aopl_python_impl.aop_value import AoPValue
from src.aopl_python_impl.definitions import AoPError


def eval_str(calc, expression, mode="num"):
    result, _ = calc.evaluate_expression(expression, mode=mode)
    return result


class TestAoPCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10)

    def test_basic_addition(self):
        self.assertEqual(eval_str(self.calculator, "a + b"), "110")

    def test_basic_multiplication(self):
        self.assertEqual(eval_str(self.calculator, "a * b"), "1000")
        self.assertEqual(eval_str(self.calculator, "a * b", mode="aop"), "a^3")

    def test_letter_juxtaposition_adds(self):
        self.assertEqual(eval_str(self.calculator, "ba"), "110")
        self.assertNotEqual(eval_str(self.calculator, "ba"), eval_str(self.calculator, "a * b"))

    def test_power_operation(self):
        self.assertEqual(eval_str(self.calculator, "a ^ b"), str(10 ** 100))
        self.assertEqual(eval_str(self.calculator, "a ^ b", mode="aop"), "a^a^2")

    def test_complex_expression(self):
        self.assertEqual(eval_str(self.calculator, "(a + b) * c"), "110000")

    def test_basic_division(self):
        self.assertEqual(eval_str(self.calculator, "c / a"), "100")

    def test_polynomial_division(self):
        self.assertEqual(eval_str(self.calculator, "(a + b) / a"), "11")
        aop_calc = AoPCalculator(base=10)
        self.assertEqual(eval_str(aop_calc, "(a + b) / a", mode="aop"), "a + 1")

    def test_constant_division(self):
        self.assertEqual(eval_str(self.calculator, "6 / 2"), "3")

    def test_carried_constant_division(self):
        self.assertEqual(eval_str(self.calculator, "10 / 2"), "5")
        self.assertEqual(eval_str(self.calculator, "(a + b) / 2"), "55")

    def test_division_cancels_multiplication(self):
        self.assertEqual(eval_str(self.calculator, "(a * b) / a"), "100")

    def test_division_left_associative(self):
        self.assertEqual(eval_str(self.calculator, "c / a / a"), "10")

    def test_division_by_zero(self):
        with self.assertRaises(AoPError) as ctx:
            self.calculator.evaluate_expression("a / 0")
        self.assertIn("Division by zero", str(ctx.exception))

    def test_inexact_division_errors(self):
        for expr in ("a / b", "(a + 1) / a", "c / 3"):
            with self.assertRaises(AoPError, msg=expr) as ctx:
                self.calculator.evaluate_expression(expr)
            self.assertIn("does not divide", str(ctx.exception), msg=expr)

    def test_trailing_equals_evaluates_left_hand_side(self):
        a_eq = eval_str(self.calculator, "a=")
        a_spaced = eval_str(self.calculator, "a =")
        three_e3 = eval_str(self.calculator, "3e3 =")
        a_plain = eval_str(self.calculator, "a")
        three_e3_plain = eval_str(self.calculator, "3e3")
        self.assertEqual(a_eq, a_plain)
        self.assertEqual(a_spaced, a_plain)
        self.assertEqual(three_e3, three_e3_plain)

    def test_mixed_bases_raise(self):
        left = AoPValue.from_number(1, 10)
        right = AoPValue.from_number(1, 2)
        with self.assertRaises(AoPError) as ctx:
            left + right
        self.assertIn("different bases", str(ctx.exception))

    def test_to_numerical_rejects_exponent_above_u32(self):
        huge = AoPValue(poly={str(2**40): 1}, base=10)
        with self.assertRaises(AoPError) as ctx:
            huge.to_numerical()
        self.assertIn("u32", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
