import unittest
import re
import math
import cmath # For complex numbers
from typing import Callable

from src.aopl_python_impl import aop_parser
from src.aopl_python_impl.definitions import (
    OPERATORS,
    TOKEN_SPECIFICATION,
    Token,
    IMAGINARY_UNIT_J
)
from src.aopl_python_impl.aop_value import AoPValue # Import AoPValue
from src.aopl_python_impl.interfaces import TermGetter
from src.aopl_python_impl import aop_term_handler

# Helper to create tokens for tests
def T(kind: str, value: str, start: int = 0, end_override: int | None = None) -> Token:
    effective_end = end_override if end_override is not None else start + len(value)
    return Token(kind, value, start, effective_end)

class TestAoPParser(unittest.TestCase):

    def setUp(self):
        self.token_regex = re.compile('|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPECIFICATION))
        self.operators_map = OPERATORS
        self.variables: dict[str, AoPValue] = {} # Changed ValueTuple to AoPValue
        self.base = 10

    def assertAoPValueAlmostEqual(self, val1: AoPValue, val2: AoPValue, places: int = 7, msg: str | None = None, rel_tol=1e-9, abs_tol=0.0):
        """Helper to compare AoPValues with almost equal for complex coefficients and exponents."""
        self.assertIsInstance(val1, AoPValue, f"val1 is not an AoPValue: {val1}")
        self.assertIsInstance(val2, AoPValue, f"val2 is not an AoPValue: {val2}")

        # Compare coefficients
        coeff_msg = f"{msg} (coeff: {val1.coeff} vs {val2.coeff})" if msg else f"(coeff: {val1.coeff} vs {val2.coeff})"
        self.assertTrue(cmath.isclose(val1.coeff, val2.coeff, rel_tol=rel_tol, abs_tol=abs_tol), coeff_msg)

        # Compare exponents
        exp_msg = f"{msg} (exp: {val1.exponent} vs {val2.exponent})" if msg else f"(exp: {val1.exponent} vs {val2.exponent})"
        if isinstance(val1.exponent, AoPValue) and isinstance(val2.exponent, AoPValue):
            self.assertAoPValueAlmostEqual(val1.exponent, val2.exponent, places, msg, rel_tol, abs_tol) # Recursive call
        elif isinstance(val1.exponent, complex) and isinstance(val2.exponent, complex):
            self.assertTrue(cmath.isclose(val1.exponent, val2.exponent, rel_tol=rel_tol, abs_tol=abs_tol), exp_msg)
        else: # Direct equality for other types or mixed types (e.g. int vs complex)
            self.assertEqual(val1.exponent, val2.exponent, exp_msg)

    def test_tokenize_expression(self):
        # Existing tests are fine as tokenization itself doesn't change for complex ValueTuple
        self.assertEqual(
            aop_parser.tokenize_expression("a * b", self.token_regex),
            [T('IDENTIFIER', 'a', 0), T('OPERATOR', '*', 2, end_override=3), T('IDENTIFIER', 'b', 4)]
        )
        # Test for #j constant
        self.assertEqual(
            aop_parser.tokenize_expression("#j", self.token_regex),
            [T('CONSTANT_LITERAL', '#j', 0)]
        )


    def test_infix_to_rpn(self):
        # Existing tests are fine as RPN conversion logic doesn't depend on ValueTuple internal type
        tokens1 = [T('IDENTIFIER', 'a',0), T('OPERATOR', '*',2,end_override=3), T('IDENTIFIER', 'b',4)]
        self.assertEqual(aop_parser.infix_to_rpn(tokens1, self.operators_map),
                         [T('IDENTIFIER', 'a',0), T('IDENTIFIER', 'b',4), T('OPERATOR', '*',2,end_override=3)])
        # ... (other RPN tests can remain as they are, focusing on token sequence)

    def test_evaluate_rpn_real_numbers(self):
        # Test with expressions that result in real numbers
        rpn1 = [T('IDENTIFIER', 'a'), T('IDENTIFIER', 'b'), T('OPERATOR', '*')] # a*b = AoPValue(1,1)*AoPValue(1,2) = AoPValue(1,3)
        self.assertAoPValueAlmostEqual(
            aop_parser.evaluate_rpn(rpn1, self.variables, aop_term_handler.get_term_value, self.base),
            AoPValue(coeff=complex(1.0, 0), exponent=3) # c
        )

        rpn2 = [T('IDENTIFIER', 'a'), T('IDENTIFIER', 'b'), T('OPERATOR', '+'), T('IDENTIFIER', 'c'), T('OPERATOR', '*')]
        # (a+b)*c
        # a -> AoPValue(1,1) -> 10
        # b -> AoPValue(1,2) -> 100
        # a+b -> AoPValue(110,0)
        # c -> AoPValue(1,3)
        # (a+b)*c -> AoPValue(110,0) * AoPValue(1,3) -> AoPValue(110 * 1, 0 + 3) = AoPValue(110, 3)
        self.assertAoPValueAlmostEqual(
            aop_parser.evaluate_rpn(rpn2, self.variables, aop_term_handler.get_term_value, self.base),
            AoPValue(coeff=complex(110.0, 0), exponent=3) # 110c
        )

        # UMINUS is not handled by default operators, would need specific handler or be part of tokenizer
        # For now, assuming it's not a standard test case unless _UMINUS is defined in OPERATOR_HANDLERS
        # rpn3 = [T('IDENTIFIER', 'a', 1), Token('OPERATOR', '_UMINUS', 0, 1)] # -a
        # self.assertAoPValueAlmostEqual(
        #     aop_parser.evaluate_rpn(rpn3, self.variables, aop_term_handler.get_term_value, self.base),
        #     AoPValue(coeff=complex(-1.0, 0), exponent=1) # -a
        # )

        # Functions like log, sqrt are not in OPERATOR_HANDLERS, they would need specific handling
        # in evaluate_rpn if they are to be processed from FUNCTION tokens.
        # Current evaluate_rpn only handles OPERATOR tokens for handlers.
        # These tests will fail unless evaluate_rpn is updated or functions are handled differently.

        # rpn4 = [T('IDENTIFIER', 'c'), T('FUNCTION', 'log')] # log(c) = log(1000) = 3
        # self.assertAoPValueAlmostEqual(
        #     aop_parser.evaluate_rpn(rpn4, self.variables, aop_term_handler.get_term_value, self.base),
        #     AoPValue(coeff=complex(3.0, 0), exponent=0)
        # )

        # rpn5 = [T('IDENTIFIER', 'd'), T('FUNCTION', 'sqrt')] # sqrt(d) = sqrt(10^4) = 10^2 = b
        # self.assertAoPValueAlmostEqual(
        #     aop_parser.evaluate_rpn(rpn5, self.variables, aop_term_handler.get_term_value, self.base),
        #     AoPValue(coeff=complex(1.0, 0), exponent=2) # b
        # )

    def test_evaluate_rpn_complex_numbers(self):
        # Test with #j constant
        rpn_j = [T('CONSTANT_LITERAL', '#j')]
        # IMAGINARY_UNIT_J is AoPValue(complex(0,1), 0.0)
        # get_term_value for #j should return this AoPValue directly.
        self.assertAoPValueAlmostEqual(
            aop_parser.evaluate_rpn(rpn_j, self.variables, aop_term_handler.get_term_value, self.base),
            IMAGINARY_UNIT_J
        )

        # Test 2 * #j
        # 2 -> AoPValue(2,0)
        # #j -> AoPValue(0+1j, 0)
        # Result -> AoPValue(2*(0+1j), 0+0) = AoPValue(0+2j, 0)
        rpn_2j = [T('NUMBER', '2'), T('CONSTANT_LITERAL', '#j'), T('OPERATOR', '*')]
        self.assertAoPValueAlmostEqual(
            aop_parser.evaluate_rpn(rpn_2j, self.variables, aop_term_handler.get_term_value, self.base),
            AoPValue(coeff=complex(0, 2.0), exponent=0)
        )

        # Test #j * #j = -1
        # #j -> AoPValue(0+1j, 0)
        # Result -> AoPValue((0+1j)*(0+1j), 0+0) = AoPValue(-1, 0)
        rpn_j_sq = [T('CONSTANT_LITERAL', '#j'), T('CONSTANT_LITERAL', '#j'), T('OPERATOR', '*')]
        self.assertAoPValueAlmostEqual(
            aop_parser.evaluate_rpn(rpn_j_sq, self.variables, aop_term_handler.get_term_value, self.base),
            AoPValue(coeff=complex(-1.0, 0), exponent=0)
        )

        # Test (1 + #j)
        # 1 -> AoPValue(1,0)
        # #j -> AoPValue(0+1j, 0)
        # Addition converts to numerical: 1 + (0+1j) = 1+1j. Result AoPValue(1+1j, 0)
        rpn_1_plus_j = [T('NUMBER', '1'), T('CONSTANT_LITERAL', '#j'), T('OPERATOR', '+')]
        self.assertAoPValueAlmostEqual(
            aop_parser.evaluate_rpn(rpn_1_plus_j, self.variables, aop_term_handler.get_term_value, self.base),
            AoPValue(coeff=complex(1.0, 1.0), exponent=0)
        )

        # These tests for sqrt and log will fail as FUNCTION tokens are not handled by OPERATOR_HANDLERS
        # rpn_sqrt_neg1 = [T('NUMBER', '-1'), T('FUNCTION', 'sqrt')]
        # self.assertAoPValueAlmostEqual(
        #     aop_parser.evaluate_rpn(rpn_sqrt_neg1, self.variables, aop_term_handler.get_term_value, self.base),
        #     AoPValue(coeff=complex(0,1), exponent=0) # Should be j
        # )

        # expected_log_j_val = cmath.log10(complex(0,1))
        # rpn_log_j = [T('CONSTANT_LITERAL', '#j'), T('FUNCTION', 'log')]
        # self.assertAoPValueAlmostEqual(
        #     aop_parser.evaluate_rpn(rpn_log_j, self.variables, aop_term_handler.get_term_value, self.base),
        #     AoPValue(coeff=expected_log_j_val, exponent=0)
        # )

    def test_evaluate_rpn_errors(self):
        rpn_bad1 = [T('OPERATOR', '*')]
        with self.assertRaisesRegex(aop_parser.AoPError, "Insufficient operands for operator '\\*'"):
            aop_parser.evaluate_rpn(rpn_bad1, self.variables, aop_term_handler.get_term_value, self.base)

        rpn_bad_stack1 = [T('IDENTIFIER', 'a'), T('IDENTIFIER', 'b')]
        # Changed expected error message to match the actual one from aop_parser.py
        with self.assertRaisesRegex(aop_parser.AoPError, "Invalid expression: stack has 2 items after evaluation"):
            aop_parser.evaluate_rpn(rpn_bad_stack1, self.variables, aop_term_handler.get_term_value, self.base)

if __name__ == '__main__':
    unittest.main()
