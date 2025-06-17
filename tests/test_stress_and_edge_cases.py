import unittest
import cmath
from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.definitions import OutputFormatMode

class TestStressAndEdgeCases(unittest.TestCase):
    def setUp(self):
        self.calc = AoP_Calculator()
        self.calc.output_format_mode = OutputFormatMode.AOP

    def test_hyper_power_with_coefficients(self):
        # Test hyper-powers where the base has a coefficient
        # (2a)^b = (2*10^1)^(10^2) = 2^100 * (10^1)^100 = (2^100) * 10^100
        # Result is AoPValue(coeff=2^100, exponent=100)
        # 2^100 = 1267650600228229401496703205376
        expected_str = "1267650600228229401496703205376*a^100"
        self.assertEqual(self.calc.evaluate_expression("(2a)^b"), expected_str)

    def test_complex_number_power_tower(self):
        # Test a complex number in a power tower
        # (#j^a)^b = ((0+1j)^(10^1))^(10^2) = ( (j^4)^2 * j^2 )^100 = (-1)^100 = 1
        self.assertEqual(self.calc.evaluate_expression("(#j^a)^b"), "1")

    def test_word_and_hyper_power_mixed(self):
        # Test a word raised to a hyper-power
        # dog = d*o*g = 10^4 * 10^15 * 10^7 = 10^26
        # dog^c = (10^26)^(10^3) = 10^(26*1000) = 10^26000
        # self.calc.evaluate_expression("dog = d*o*g") # Variable assignment not directly supported by evaluate_expression
        self.assertEqual(self.calc.evaluate_expression("(d*o*g)^c"), "a^26000")


    def test_deeply_nested_expression(self):
        # Test a complex expression with deep nesting and mixed operators
        self.assertEqual(self.calc.evaluate_expression("(a*b + c*d)^2"), "100020001000000")

    def test_right_associativity_challenge(self):
        # Test the right-associative operator for correctness
        self.calc.set_power_associativity('right') # Default is right, so this is just for emphasis
        # a**b**c -> a^(b^c) = a^(10^2000)
        self.assertEqual(self.calc.evaluate_expression("a**b**c"), "a^(a^2000)")
