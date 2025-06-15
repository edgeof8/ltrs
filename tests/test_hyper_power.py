# tests/test_hyper_power.py

import unittest
from src.aopl_python_impl.aop_calculator import AoPCalculator
from src.aopl_python_impl.definitions import OutputFormatMode

class TestHyperPower(unittest.TestCase):
    def setUp(self):
        self.calculator = AoPCalculator(base=10, output_mode=OutputFormatMode.AOP)

    def test_hyper_power(self):
        result = self.calculator.calculate("a^b^c^d^e^f^g^h^i^j^k")
        self.assertEqual(result, "a^mzz")

if __name__ == '__main__':
    unittest.main()
