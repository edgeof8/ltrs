import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator


def eval_str(calc, expression, mode="aop"):
    result, _ = calc.evaluate_expression(expression, mode=mode)
    return result


class TestFinalCorrectness(unittest.TestCase):
    def setUp(self):
        self.calc = AoP_Calculator()

    def test_basic_symbolic(self):
        self.assertEqual(eval_str(self.calc, "a*b", mode="num"), "1000")
        self.assertEqual(eval_str(self.calc, "a*b"), "c")
        self.assertEqual(eval_str(self.calc, "10a*c", mode="num"), "100000")

    def test_numerical_power(self):
        self.assertEqual(eval_str(self.calc, "b^a", mode="num"), str(100 ** 10))
        self.assertEqual(eval_str(self.calc, "c^a", mode="num"), str(1000 ** 10))

    def test_hyper_power(self):
        self.assertEqual(eval_str(self.calc, "a^b", mode="num"), str(10 ** 100))
        self.assertEqual(eval_str(self.calc, "a^b"), "Z")

    def test_tetration(self):
        self.assertEqual(eval_str(self.calc, "a^b^c"), "a^(a^(2*c))")
        self.assertEqual(eval_str(self.calc, "a**b**c"), "a^(a^(2*c))")
