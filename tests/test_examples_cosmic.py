# tests/test_examples_cosmic.py

import json
import os
import tempfile
import unittest
from pathlib import Path

from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.aop_parser import tokenize_expression, Parser


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class TestExampleCosmicFiles(unittest.TestCase):
    def test_examples_are_valid_and_expressions_parse(self):
        files = sorted(EXAMPLES.glob("*.cosmic"))
        self.assertGreaterEqual(len(files), 3, "expected local example canvases")
        for path in files:
            with self.subTest(path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIn("nodes", data)
                self.assertIn("base", data)
                calc = AoP_Calculator(
                    base=data["base"],
                    cache_file=os.path.join(tempfile.mkdtemp(), "c.json"),
                )
                calc.cache = None
                for node in data["nodes"]:
                    expr = node["expression"]
                    self.assertIsNotNone(Parser(tokenize_expression(expr)).parse())
                    mode = node.get("output_mode", "num")
                    result, _ = calc.evaluate_expression(expr, mode=mode)
                    self.assertFalse(str(result).startswith("Error:"), result)
