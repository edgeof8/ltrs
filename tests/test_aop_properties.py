# tests/test_aop_properties.py
"""Small expressions compared to Python int in the same base."""

import os
import random
import tempfile
import unittest

from src.aopl_python_impl.aop_calculator import AoP_Calculator

_ATOMS = ("a", "b", "c", "1", "2", "3")
_LETTERS = {"a": 1, "b": 2, "c": 3}


def _python_value(expr: str, base: int) -> int:
    env = {name: base ** exp for name, exp in _LETTERS.items()}
    return int(eval(expr, {"__builtins__": {}}, env))


def _random_expr(rng: random.Random, depth: int) -> str:
    if depth <= 0:
        return rng.choice(_ATOMS)
    left = _random_expr(rng, depth - 1)
    right = _random_expr(rng, depth - 1)
    op = rng.choice(("+", "*"))
    return f"({left} {op} {right})"


class TestAoPProperties(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _calc(self, base: int) -> AoP_Calculator:
        return AoP_Calculator(
            base=base, cache_file=os.path.join(self.tmp.name, f"p{base}.json")
        )

    def test_fixed_cases_match_python_int(self):
        calc = self._calc(10)
        cases = ("a + b", "a * b", "(a + 1) * b", "a + 2", "(2 + 3) * a")
        for expr in cases:
            with self.subTest(expr=expr):
                got, _ = calc.evaluate_expression(expr, mode="num")
                self.assertEqual(int(got), _python_value(expr, 10), expr)

    def test_random_plus_times_against_python_int(self):
        rng = random.Random(20260901)
        for base in (10, 2, 16):
            calc = self._calc(base)
            for _ in range(40):
                expr = _random_expr(rng, depth=3)
                got, _ = calc.evaluate_expression(expr, mode="num")
                self.assertEqual(int(got), _python_value(expr, base), f"{expr} base={base}")
