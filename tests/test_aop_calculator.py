# tests/test_aop_calculator.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator # Renamed import
# Removed OutputFormatMode import as it's no longer used in AoP_Calculator

class TestAoPCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10) # Removed output_mode parameter

    def test_basic_addition(self):
        result = self.calculator.evaluate_expression("a + b") # Changed calculate to evaluate_expression
        self.assertEqual(result, "110") # a+b = 10+100 = 110

    def test_basic_multiplication(self):
        result = self.calculator.evaluate_expression("a * b") # Changed calculate to evaluate_expression
        self.assertEqual(result, "c") # a*b = 10^1 * 10^2 = 10^3 = c

    def test_power_operation(self):
        result = self.calculator.evaluate_expression("a ^ b") # Changed calculate to evaluate_expression
        self.assertEqual(result, "a^100") # (10^1)^(10^2) = 10^100

    def test_complex_expression(self):
        result = self.calculator.evaluate_expression("(a + b) * c") # Changed calculate to evaluate_expression
        self.assertEqual(result, "110*c") # (10+100)*10^3 = 110 * 10^3 = 110c

    def test_basic_division(self):
        result, _ = self.calculator.evaluate_expression("c / a")
        self.assertEqual(result, "100")  # c/a = 10^3 / 10^1 = 10^2

    def test_polynomial_division(self):
        result, _ = self.calculator.evaluate_expression("(a + b) / a")
        self.assertEqual(result, "11")  # (10 + 100) / 10 = 11
        # Fresh instance: the calculator cache path is mode-specific and can
        # UnboundLocalError if the same expression is re-evaluated in another mode.
        aop_calc = AoPCalculator(base=10)
        aop_result, _ = aop_calc.evaluate_expression("(a + b) / a", mode="aop")
        self.assertEqual(aop_result, "a + 1")

    def test_constant_division(self):
        result, _ = self.calculator.evaluate_expression("6 / 2")
        self.assertEqual(result, "3")

    def test_carried_constant_division(self):
        # 10 is stored as the monomial X after carry; formal X/2 is not in Z[X],
        # but the integer 10 divides by 2.
        result, _ = self.calculator.evaluate_expression("10 / 2")
        self.assertEqual(result, "5")
        result, _ = self.calculator.evaluate_expression("(a + b) / 2")
        self.assertEqual(result, "55")

    def test_division_cancels_multiplication(self):
        result, _ = self.calculator.evaluate_expression("(a * b) / a")
        self.assertEqual(result, "100")  # b

    def test_division_left_associative(self):
        result, _ = self.calculator.evaluate_expression("c / a / a")
        self.assertEqual(result, "10")  # (c/a)/a = b/a = a

    def test_division_by_zero(self):
        result, ast = self.calculator.evaluate_expression("a / 0")
        self.assertTrue(result.startswith("Error:"), result)
        self.assertIn("Division by zero", result)
        self.assertIsNone(ast)

    def test_inexact_division_errors(self):
        for expr in ("a / b", "(a + 1) / a", "c / 3"):
            result, ast = self.calculator.evaluate_expression(expr)
            self.assertIsNone(ast, msg=expr)
            self.assertTrue(result.startswith("Error:"), msg=expr)
            self.assertIn("does not divide", result, msg=expr)

    def test_trailing_equals_evaluates_left_hand_side(self):
        a_eq, _ = self.calculator.evaluate_expression("a=")
        a_spaced, _ = self.calculator.evaluate_expression("a =")
        three_e3, _ = self.calculator.evaluate_expression("3e3 =")
        a_plain, _ = self.calculator.evaluate_expression("a")
        three_e3_plain, _ = self.calculator.evaluate_expression("3e3")
        self.assertEqual(a_eq, a_plain)
        self.assertEqual(a_spaced, a_plain)
        self.assertEqual(three_e3, three_e3_plain)
        self.assertFalse(a_eq.startswith("Error:"))
        self.assertFalse(three_e3.startswith("Error:"))

if __name__ == '__main__':
    unittest.main()
