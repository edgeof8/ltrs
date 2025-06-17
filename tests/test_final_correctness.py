import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.definitions import OutputFormatMode

class TestFinalCorrectness(unittest.TestCase):
    def setUp(self):
        self.calc = AoP_Calculator()
        self.calc.output_format_mode = OutputFormatMode.AOP

    def test_basic_symbolic(self):
        self.assertEqual(self.calc.evaluate_expression("a*b"), "c")
        self.assertEqual(self.calc.evaluate_expression("10a*c"), "e")

    def test_numerical_power(self):
        # These should be calculated numerically and then formatted back to AoP
        self.assertEqual(self.calc.evaluate_expression("b^a"), "t")
        self.assertEqual(self.calc.evaluate_expression("c^a"), "a^30")

    def test_hyper_power(self):
        # These overflow numerical calculation and are handled symbolically
        self.assertEqual(self.calc.evaluate_expression("a^b"), "a^100") # (10^1)^(10^2) = 10^100
        # j^j = 10^(10^11). Formatter output for AoPValue(1, 10^11) is a^<number>
        self.assertEqual(self.calc.evaluate_expression("j^j"), "a^100000000000")

    def test_tetration(self):
        # Default associativity for ^ is right.
        # a^b^c -> a^(b^c) = a^( (10^2)^(10^3) ) = a^( 10^(2*1000) ) = a^(10^2000)
        self.assertEqual(self.calc.evaluate_expression("a^b^c"), "a^(a^2000)")
        # a^b^c^d -> a^(b^(c^d))
        # c^d = (10^3)^(10^4) = 10^(3*10000) = 10^30000
        # b^(c^d) = (10^2)^(10^30000) = 10^(2*10^30000)
        # a^(b^(c^d)) = (10^1)^(10^(2*10^30000)) = 10^(10^(2*10^30000))
        self.assertEqual(self.calc.evaluate_expression("a^b^c^d"), "a^(a^(2*a^30000))") # Expecting detailed symbolic form

        # Test right-associative tetration (already default for aop_parser.py)
        self.calc.set_power_associativity('right') # Explicitly set for clarity, though default
        # a**b**c is same as a^b^c if ** is alias for ^
        self.assertEqual(self.calc.evaluate_expression("a**b**c"), "a^(a^2000)") # Expecting a^(a^2000), not a^a^2c for now
