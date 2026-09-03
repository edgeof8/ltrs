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
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        cmd = [sys.executable, "-m", "aopl_python_impl.aop_calculator_cli"] + args
        process = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT))
        return process.stdout.strip(), process.stderr.strip(), process.returncode

    def test_basic_expression_num_mode(self):
        stdout, stderr, returncode = self.run_cli(["a * b", "--no-cache"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "1000")

    def test_aop_mode(self):
        stdout, stderr, returncode = self.run_cli(["a * b", "--mode", "aop", "--no-cache"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "c")

    def test_juxtaposition_adds(self):
        stdout, stderr, returncode = self.run_cli(["ba", "--no-cache"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "110")

    def test_base_option(self):
        stdout, stderr, returncode = self.run_cli(["a", "--base", "2", "--mode", "num", "--no-cache"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "2")

    def test_error_expression(self):
        stdout, stderr, returncode = self.run_cli(["a / 0", "--no-cache"])
        combined = stdout + stderr
        self.assertTrue("Error" in combined or returncode != 0, combined)

    def test_debug_prints_performance_timer(self):
        stdout, stderr, returncode = self.run_cli(["a + b", "--debug", "--no-cache"])
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Performance", stdout)

    def test_without_debug_omits_performance_timer(self):
        stdout, stderr, returncode = self.run_cli(["a + b", "--no-cache"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "110")
        self.assertNotIn("Performance", stdout)

    def test_gcd(self):
        stdout, stderr, returncode = self.run_cli(["c gcd a", "--mode", "aop", "--no-cache"])
        self.assertEqual(returncode, 0, stderr)
        self.assertEqual(stdout, "a")


class TestAoPRepl(unittest.TestCase):
    def test_mode_persists_for_next_expression(self):
        from src.aopl_python_impl.aop_calculator import AoP_Calculator
        from src.aopl_python_impl.aop_calculator_cli import handle_repl_command
        from unittest.mock import patch

        calc = AoP_Calculator(base=10)
        session = {"mode": "num"}
        printed = []
        with patch("builtins.print", side_effect=lambda *a, **_k: printed.append(" ".join(str(x) for x in a))):
            handle_repl_command("!mode aop", calc, None, session)
            handle_repl_command("a * b", calc, None, session)
        self.assertEqual(session["mode"], "aop")
        self.assertIn("c", printed)
