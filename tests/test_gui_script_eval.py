# tests/test_gui_script_eval.py

import os
import tempfile
import unittest

from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.gui.graph_logic import graph_has_cycle
from src.aopl_python_impl.gui.script_eval import run_isolated_script


class _Node:
    def __init__(self, defined, deps):
        self.defined_variable = defined
        self.dependencies = set(deps)


class TestGuiScriptEval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calc = AoP_Calculator(
            base=10, cache_file=os.path.join(self.tmp.name, "c.json")
        )
        self.calc.cache = None

    def tearDown(self):
        self.tmp.cleanup()

    def test_multiline_commits_variables_on_success(self):
        result = run_isolated_script(self.calc, "$x = a\n$x + 1")
        self.assertEqual(result, "11")
        self.assertIn("$x", self.calc.variables)

    def test_error_does_not_commit_partial_variables(self):
        run_isolated_script(self.calc, "$x = a\n$x / 0")
        self.assertNotIn("$x", self.calc.variables)

    def test_aop_mode(self):
        result = run_isolated_script(self.calc, "a * b", mode="aop")
        self.assertEqual(result, "c")

    def test_cycle_between_two_definitions(self):
        n1 = _Node("$x", ["y"])
        n2 = _Node("$y", ["x"])
        defs = {n1: "$x", n2: "$y"}
        self.assertTrue(graph_has_cycle(defs))

    def test_acyclic_definitions(self):
        n1 = _Node("$x", [])
        n2 = _Node("$y", ["x"])
        defs = {n1: "$x", n2: "$y"}
        self.assertFalse(graph_has_cycle(defs))
