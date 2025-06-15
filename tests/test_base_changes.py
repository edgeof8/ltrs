import unittest
import math
from src.aopl_python_impl.aop_calculator import AoP_Calculator

class TestBaseChanges(unittest.TestCase):

    def setUp(self):
        self.calculator = AoP_Calculator() # Default base 10

    def test_simple_base_change_and_calculation(self):
        self.calculator.base = 10 # Explicitly set for clarity
        self.assertEqual(self.calculator.evaluate_expression("a"), "a")

        self.calculator.base = 5
        self.assertEqual(self.calculator.base, 5)

        # If a term evaluates to (1.0, exponent_of_letter), it's formatted as the letter.
        self.assertEqual(self.calculator.evaluate_expression("a"), "a")
        self.assertEqual(self.calculator.evaluate_expression("a+0"), "5") # Check numerical value
        self.assertEqual(self.calculator.evaluate_expression("b"), "b")
        self.assertEqual(self.calculator.evaluate_expression("b+0"), "25")
        self.assertEqual(self.calculator.evaluate_expression("c"), "c")
        self.assertEqual(self.calculator.evaluate_expression("c+0"), "125")

        self.assertEqual(self.calculator.evaluate_expression("a * b"), "c")
        self.assertEqual(self.calculator.evaluate_expression("c / a"), "b")
        self.assertEqual(self.calculator.evaluate_expression("2a * 3b"), "750")


    def test_variable_clearing_on_base_change(self):
        self.calculator.base = 10
        self.calculator.evaluate_expression("x = a * b")
        self.assertEqual(self.calculator.evaluate_expression("x"), "c")
        self.assertTrue("x" in self.calculator.variables)

        self.calculator.base = 2 # This should trigger variables.clear()
        self.assertEqual(self.calculator.base, 2)
        self.assertFalse("x" in self.calculator.variables, "Variables were not cleared on base change")

        self.assertEqual(self.calculator.evaluate_expression("a"), "a")
        self.assertEqual(self.calculator.evaluate_expression("a+0"), "2")
        self.assertEqual(self.calculator.evaluate_expression("c"), "c")
        self.assertEqual(self.calculator.evaluate_expression("c+0"), "8")
        self.assertEqual(self.calculator.evaluate_expression("a * c"), "d")


    def test_formatting_with_different_bases(self):
        self.calculator.base = 2
        self.assertEqual(self.calculator.evaluate_expression("10"), "10")
        self.assertEqual(self.calculator.evaluate_expression("d"), "d")
        self.assertEqual(self.calculator.evaluate_expression("d+0"), "16")

        self.calculator.base = 16
        self.assertEqual(self.calculator.evaluate_expression("a"), "a")
        self.assertEqual(self.calculator.evaluate_expression("a+0"), "16")
        self.assertEqual(self.calculator.evaluate_expression("b"), "b")
        self.assertEqual(self.calculator.evaluate_expression("b+0"), "256")
        self.assertEqual(self.calculator.evaluate_expression("255"), "255")


    def test_constants_with_base_change(self):
        self.calculator.base = 10
        pi_val_base10 = float(self.calculator.evaluate_expression("#pi"))
        self.assertAlmostEqual(pi_val_base10, math.pi)

        self.calculator.base = 3
        pi_val_base3 = float(self.calculator.evaluate_expression("#pi"))
        self.assertAlmostEqual(pi_val_base3, math.pi)

        self.assertAlmostEqual(float(self.calculator.evaluate_expression("#pi + a")), math.pi + 3)


if __name__ == '__main__':
    unittest.main()
