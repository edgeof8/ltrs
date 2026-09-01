import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.aop_formatter import group_characters


def eval_str(calc, expression, mode="aop"):
    result, _ = calc.evaluate_expression(expression, mode=mode)
    return result


class TestStressAndEdgeCases(unittest.TestCase):
    def setUp(self):
        self.calc = AoP_Calculator()

    def test_hyper_power_with_coefficients(self):
        result = eval_str(self.calc, "(2a)^b")
        self.assertIn("1267650600228229401496703205376", result)

    def test_word_and_hyper_power_mixed(self):
        self.assertEqual(eval_str(self.calc, "(d*o*g)^c"), "a^(2*d + 6*c)")

    def test_deeply_nested_expression(self):
        result, _ = self.calc.evaluate_expression("(a*b + c*d)^2", mode="num")
        self.assertEqual(result, group_characters("100020001000000"))

    def test_right_associativity_challenge(self):
        self.assertEqual(eval_str(self.calc, "a**b**c"), "a^(a^(2*c))")
