import unittest
from src.aopl_python_impl.aop_calculator import AoP_Calculator


def eval_str(calc, expression, mode="aop"):
    result, _ = calc.evaluate_expression(expression, mode=mode)
    return result


class TestBaseChanges(unittest.TestCase):
    def test_simple_base_change_and_calculation(self):
        calc_base5 = AoP_Calculator(base=5)
        self.assertEqual(eval_str(calc_base5, "a+0", mode="num"), "5")
        self.assertEqual(eval_str(calc_base5, "b+0", mode="num"), "25")
        self.assertEqual(eval_str(calc_base5, "a*b", mode="num"), "125")
