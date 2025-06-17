import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator

class TestBaseChanges(unittest.TestCase):
    def setUp(self):
        self.calculator = AoP_Calculator() # Default calculator for other tests if any

    def test_simple_base_change_and_calculation(self):
        # Re-initialize calculator for this test with base 5
        # This ensures letter maps are also for base 5
        calc_base5 = AoP_Calculator(base=5)
        calc_base5.output_format_mode = self.calculator.output_format_mode # Preserve mode if needed, or set AOP

        # In base 5, 'a' is 5^1. 'a+0' -> AoPValue(5,0) -> simplify -> AoPValue(1,1) base 5 -> formats to 'a'
        self.assertEqual(calc_base5.evaluate_expression("a+0"), "a")
        # In base 5, 'b' is 5^2. 'b+0' -> AoPValue(25,0) -> simplify -> AoPValue(1,2) base 5 -> formats to 'b'
        self.assertEqual(calc_base5.evaluate_expression("b+0"), "b")
        # a*b = 5^1 * 5^2 = 5^3. In base 5, AoPValue(1,3) is 'c'.
        self.assertEqual(calc_base5.evaluate_expression("a*b"), "c")
