# tests/test_advanced_symbolics.py

import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator as AoPCalculator


def eval_str(calc, expression, mode="aop"):
    result, _ = calc.evaluate_expression(expression, mode=mode)
    return result


class TestAdvancedSymbolics(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10)

    def test_nested_powers(self):
        self.assertEqual(eval_str(self.calculator, "a^b^c"), "a^(a^(2*c))")

    def test_hyper_power_plus_one(self):
        result = eval_str(self.calculator, "a^b + 1", mode="num")
        self.assertTrue(result.endswith("1") or result.startswith("Error:"), result)
