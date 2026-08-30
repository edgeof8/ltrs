# tests/test_aop_calculator_cli.py

import os
import sys
import unittest
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"


class TestAoPCalculatorCLI(unittest.TestCase):
    def run_cli(self, args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "aopl_python_impl.aop_calculator_cli"] + args
        process = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT))
        return process.stdout.strip(), process.stderr.strip(), process.returncode

    def test_basic_expression_num_mode(self):
        stdout, stderr, returncode = self.run_cli(["a * b"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "1000")

    def test_aop_mode(self):
        stdout, stderr, returncode = self.run_cli(["a * b", "--mode", "aop"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "a^3")

    def test_juxtaposition_adds(self):
        stdout, stderr, returncode = self.run_cli(["ba"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "110")

    def test_base_option(self):
        stdout, stderr, returncode = self.run_cli(["a", "--base", "2", "--mode", "num"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "2")

    def test_error_expression(self):
        stdout, stderr, returncode = self.run_cli(["a / 0"])
        combined = stdout + stderr
        self.assertTrue("Error" in combined or returncode != 0, combined)
