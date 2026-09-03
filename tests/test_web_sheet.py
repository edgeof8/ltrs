# tests/test_web_sheet.py

import unittest

from src.aopl_python_impl.webgui.sheet import (
    _named_assignments,
    canonicalize_cell_vars,
    evaluate_sheet,
    format_addr,
    normalize_addr,
    parse_addr,
    strip_leading_equals,
)


class TestSheetAddresses(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(parse_addr("A1"), (0, 0))
        self.assertEqual(parse_addr("B10"), (1, 9))
        self.assertEqual(format_addr(0, 0), "A1")
        self.assertEqual(format_addr(25, 0), "Z1")
        self.assertEqual(normalize_addr("a1"), "A1")
        self.assertEqual(normalize_addr("aa2"), "AA2")

    def test_leading_equals_and_cell_vars(self):
        self.assertEqual(strip_leading_equals("=$A1 + 1"), "$A1 + 1")
        self.assertEqual(strip_leading_equals("== 1"), "== 1")
        self.assertEqual(canonicalize_cell_vars("$b1 + $x"), "$B1 + $x")

    def test_equality_is_not_assignment(self):
        self.assertEqual(_named_assignments("$A1 == c"), [])
        self.assertEqual(_named_assignments("$x = a"), ["$x"])


class TestSheetEvaluate(unittest.TestCase):
    def test_cell_binds_and_fingerprint(self):
        result = evaluate_sheet(10, {"A1": {"expr": "a * b", "output_mode": "num"}})
        cell = result.cells["A1"]
        self.assertEqual(cell.primary, "1000")
        self.assertEqual(cell.secondary, "c")
        self.assertEqual(result.variables["$A1"], "1000")

    def test_dependent_cells(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "a * b"},
                "B1": {"expr": "$A1 + 1"},
            },
        )
        self.assertEqual(result.cells["B1"].primary, "1001")

    def test_leading_equals_formula(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "a * b"},
                "B1": {"expr": "=$A1 + 1"},
            },
        )
        self.assertEqual(result.cells["B1"].primary, "1001")

    def test_multiline_script_in_cell(self):
        result = evaluate_sheet(
            10,
            {"A1": {"expr": "$x = a\n$x * b"}},
        )
        self.assertEqual(result.cells["A1"].primary, "1000")
        self.assertEqual(result.variables["$x"], "10")
        self.assertEqual(result.variables["$A1"], "1000")

    def test_named_variable_and_cell_alias(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "$x = c"},
                "B1": {"expr": "$x / a"},
            },
        )
        self.assertEqual(result.cells["B1"].primary, "100")
        self.assertIn("$x", result.variables)
        self.assertIn("$A1", result.variables)

    def test_equality_true_false(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "a * b"},
                "B1": {"expr": "$A1 == c"},
                "C1": {"expr": "$A1 == 1"},
            },
        )
        self.assertEqual(result.cells["B1"].primary, "True")
        self.assertEqual(result.cells["C1"].primary, "False")

    def test_aop_primary_mode(self):
        result = evaluate_sheet(10, {"A1": {"expr": "a * b", "output_mode": "aop"}})
        self.assertEqual(result.cells["A1"].primary, "c")
        self.assertEqual(result.cells["A1"].secondary, "1000")

    def test_cycle_is_error(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "$B1 + 1"},
                "B1": {"expr": "$A1 + 1"},
            },
        )
        self.assertTrue(result.cells["A1"].error)
        self.assertIn("cycle", result.cells["A1"].primary.lower())
        self.assertTrue(result.cells["B1"].error)

    def test_error_does_not_poison_unrelated_cell(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "a / 0"},
                "C1": {"expr": "5"},
            },
        )
        self.assertTrue(result.cells["A1"].error)
        self.assertEqual(result.cells["C1"].primary, "5")
        self.assertNotIn("$A1", result.variables)

    def test_duplicate_named_variable(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "$x = a"},
                "B1": {"expr": "$x = b"},
            },
        )
        self.assertFalse(result.cells["A1"].error)
        self.assertTrue(result.cells["B1"].error)
        self.assertIn("already defined", result.cells["B1"].primary)

    def test_reserved_cell_name(self):
        result = evaluate_sheet(
            10,
            {
                "A1": {"expr": "$B1 = a"},
                "B1": {"expr": "b"},
            },
        )
        self.assertTrue(result.cells["A1"].error)
        self.assertEqual(result.cells["B1"].primary, "100")

    def test_setbase_command_applies_before_formulas(self):
        result = evaluate_sheet(
            10,
            {
                "Z1": {"expr": "/setbase 2"},
                "A1": {"expr": "a"},
            },
        )
        self.assertEqual(result.base, 2)
        self.assertEqual(result.cells["A1"].primary, "2")
        self.assertTrue(result.cells["Z1"].command)

    def test_help_command(self):
        result = evaluate_sheet(10, {"A1": {"expr": "/help"}})
        self.assertTrue(result.cells["A1"].command)
        self.assertIn("$A1", result.cells["A1"].primary)


class TestSheetApi(unittest.TestCase):
    def test_evaluate_endpoint(self):
        try:
            from fastapi.testclient import TestClient
            from aopl_python_impl.webgui.server import app
        except Exception:
            self.skipTest("fastapi test client not available")
        if app is None:
            self.skipTest("fastapi not installed")
        client = TestClient(app)
        response = client.post(
            "/api/evaluate",
            json={"base": 10, "cells": {"A1": {"expr": "a * b", "output_mode": "num"}}},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cells"]["A1"]["primary"], "1000")
        self.assertEqual(data["cells"]["A1"]["secondary"], "c")
        health = client.get("/api/health")
        self.assertEqual(health.json()["ok"], True)
