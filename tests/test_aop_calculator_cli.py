# tests/test_aop_calculator_cli.py

import unittest
import subprocess
import os

class TestAoPCalculatorCLI(unittest.TestCase):
    def run_cli(self, args):
        cmd = ["python", "-m", "src.aopl_python_impl.aop_calculator_cli"] + args
        process = subprocess.run(cmd, capture_output=True, text=True)
        return process.stdout.strip(), process.stderr.strip(), process.returncode

    def test_basic_expression(self):
        stdout, stderr, returncode = self.run_cli(["a * b"])
        self.assertEqual(stdout, "c")
        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, "")

    def test_base_option(self):
        stdout, stderr, returncode = self.run_cli(["a", "--base", "2"])
        self.assertEqual(stdout, "a") # 'a' in base 2 is 2^1
        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, "")

    def test_mode_option(self):
        stdout, stderr, returncode = self.run_cli(["a", "--mode", "sci"]) # 'a' is 10^1. SCI mode currently like NUM.
        self.assertEqual(stdout, "10")
        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, "")

    def test_precision_option(self):
        stdout, stderr, returncode = self.run_cli(["2.1234567a", "--mode", "num", "--precision", "3"])
        self.assertEqual(stdout, "21.2")
        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, "")

    def test_invalid_expression(self):
        stdout, stderr, returncode = self.run_cli(["invalid^expression"])
        self.assertNotEqual(returncode, 0)
        # The CLI now prints the specific error message to stderr
        self.assertEqual(stderr, "Error: Unexpected character: '^'") # Exact match expected

if __name__ == '__main__':
    unittest.main()
