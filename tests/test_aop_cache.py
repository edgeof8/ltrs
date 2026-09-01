# tests/test_aop_cache.py

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.aopl_python_impl.aop_calculator import AoP_Calculator
from src.aopl_python_impl.aop_cache import CACHE_VERSION, encode_aop_value, poly_key
from src.aopl_python_impl.aop_logger import disable_debug_timer, is_debug_timer_enabled
from src.aopl_python_impl.aop_value import AoPValue


class TestAoPCache(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.tmpdir.name, "cache_v3.json")
        self.calc = AoP_Calculator(base=10, cache_file=self.cache_path)

    def tearDown(self):
        disable_debug_timer()
        self.tmpdir.cleanup()

    def test_poly_key_includes_base_and_canonical_terms(self):
        ten = AoPValue.from_literal("a", base=10)
        two = AoPValue.from_literal("a", base=2)
        self.assertNotEqual(poly_key(encode_aop_value(ten)), poly_key(encode_aop_value(two)))

    def test_second_eval_uses_formatted_cache(self):
        first, _ = self.calc.evaluate_expression("a * b", mode="num")
        self.assertEqual(first, "1000")
        with patch(
            "src.aopl_python_impl.aop_calculator.evaluate_ast",
            side_effect=AssertionError("should not re-evaluate"),
        ):
            second, _ = self.calc.evaluate_expression("a * b", mode="num")
        self.assertEqual(second, "1000")

    def test_other_mode_formats_from_stored_poly(self):
        self.calc.evaluate_expression("a * b", mode="num")
        with patch(
            "src.aopl_python_impl.aop_calculator.evaluate_ast",
            side_effect=AssertionError("should not re-evaluate"),
        ):
            aop, _ = self.calc.evaluate_expression("a * b", mode="aop")
        self.assertEqual(aop, "a^3")

    def test_saved_cache_has_no_pickle(self):
        self.calc.evaluate_expression("ba", mode="num")
        self.calc.save_cache()
        with open(self.cache_path, encoding="utf-8") as f:
            data = json.load(f)
        blob = json.dumps(data)
        self.assertEqual(data["version"], CACHE_VERSION)
        self.assertNotIn("raw_pickle", blob)
        self.assertNotIn("gASV", blob)

    def test_ignores_pickle_v2_cache_file(self):
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "10": {
                        "a * b": {
                            "raw_pickle": "gASVnot-real",
                            "num": "should-not-use",
                        }
                    }
                },
                f,
            )
        calc = AoP_Calculator(base=10, cache_file=self.cache_path)
        result, _ = calc.evaluate_expression("a * b", mode="num")
        self.assertEqual(result, "1000")

    def test_variables_are_not_keyed_as_pure_expressions(self):
        self.calc.evaluate_expression("$x = a")
        first, _ = self.calc.evaluate_expression("$x")
        self.calc.evaluate_expression("$x = b")
        second, _ = self.calc.evaluate_expression("$x")
        self.assertEqual(first, "10")
        self.assertEqual(second, "100")

    def test_debug_timer_off_by_default(self):
        self.assertFalse(is_debug_timer_enabled())
        with patch("src.aopl_python_impl.aop_calculator.DebugTimer") as timer_cls:
            timer_cls.return_value.lap = lambda *_a, **_k: None
            timer_cls.return_value.report = lambda *_a, **_k: None
            self.calc.evaluate_expression("a + b")
        timer_cls.assert_called_with(enabled=False)


if __name__ == "__main__":
    unittest.main()
