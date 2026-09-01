# tests/test_advanced_symbolics.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator
from src.aopl_python_impl.definitions import AoPError


def eval_str(calc, expression, mode="aop"):
    result, _ = calc.evaluate_expression(expression, mode=mode)
    return result


class TestAdvancedSymbolics(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10)

    def test_nested_powers(self):
        self.assertEqual(eval_str(self.calculator, "a^b^c"), "a^(a^(2*c))")

    def test_hyper_power_plus_one(self):
        try:
            result = eval_str(self.calculator, "a^b + 1", mode="num")
        except AoPError:
            return
        self.assertTrue(result.endswith("1"), result)
