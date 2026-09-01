# tests/test_associativity.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator


def eval_str(calc, expression, mode="aop"):
    result, _ = calc.evaluate_expression(expression, mode=mode)
    return result


class TestAssociativity(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10)

    def test_power_associativity(self):
        self.assertEqual(eval_str(self.calculator, "a^b^c"), "a^(a^(2*c))")

    def test_multiplication_associativity(self):
        self.assertEqual(eval_str(self.calculator, "a * b * c", mode="num"), "10,00000")
        self.assertEqual(eval_str(self.calculator, "a * b * c"), "f")
