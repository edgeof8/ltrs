import unittest
from src.aopl_python_impl.aop_value import AoPValue


class TestAoPOperations(unittest.TestCase):
    def test_add_values(self):
        v1 = AoPValue.from_literal("a")
        v2 = AoPValue.from_literal("b")
        self.assertEqual((v1 + v2).to_numerical(), 110)

    def test_multiply_values(self):
        v1 = AoPValue.from_literal("a")
        v2 = AoPValue.from_literal("b")
        self.assertEqual((v1 * v2).to_numerical(), 1000)

    def test_power_value_simple(self):
        base_val = AoPValue.from_literal("a")
        power_val = AoPValue.from_literal("b")
        result = base_val ** power_val
        self.assertEqual(result.to_numerical(), 10 ** 100)
