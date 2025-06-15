import unittest
import re
import math
import cmath # For complex numbers
from typing import Callable

from src.aopl_python_impl import aop_parser
from src.aopl_python_impl.definitions import (
    ValueTuple,
    OPERATORS,
    TOKEN_SPECIFICATION,
    Token,
    IMAGINARY_UNIT_J
)
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
        self.variables: dict[str, ValueTuple] = {}
        self.base = 10

    def assertValueTupleAlmostEqual(self, vt1: ValueTuple, vt2: ValueTuple, places: int = 7, msg: str | None = None, rel_tol=1e-9, abs_tol=0.0):
        """Helper to compare ValueTuples with almost equal for complex coefficients."""
        self.assertIsInstance(vt1, tuple)
        self.assertIsInstance(vt2, tuple)
        self.assertEqual(len(vt1), 2)
        self.assertEqual(len(vt2), 2)
        self.assertIsInstance(vt1[0], complex, f"First coeff not complex: {vt1[0]}")
        self.assertIsInstance(vt2[0], complex, f"Second coeff not complex: {vt2[0]}")

        coeff_msg = f"{msg} (coeff: {vt1[0]} vs {vt2[0]})" if msg else f"(coeff: {vt1[0]} vs {vt2[0]})"
        exp_msg = f"{msg} (exp: {vt1[1]} vs {vt2[1]})" if msg else f"(exp: {vt1[1]} vs {vt2[1]})"

        self.assertTrue(cmath.isclose(vt1[0], vt2[0], rel_tol=rel_tol, abs_tol=abs_tol), coeff_msg)
        self.assertEqual(vt1[1], vt2[1], exp_msg)

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
        rpn1 = [T('IDENTIFIER', 'a'), T('IDENTIFIER', 'b'), T('OPERATOR', '*')] # a*b = (1+0j,1)*(1+0j,2) = (1+0j,3)
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn1, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(1.0, 0), 3) # c
        )

        rpn2 = [T('IDENTIFIER', 'a'), T('IDENTIFIER', 'b'), T('OPERATOR', '+'), T('IDENTIFIER', 'c'), T('OPERATOR', '*')]
        # (a+b)*c = ((10+0j,0) + (100+0j,0)) * (1000+0j,0) = (110+0j,0) * (1000+0j,0)
        # = (110000+0j, 0)
        # Note: aop_term_handler.get_term_value for 'a' is (1+0j,1), 'b' is (1+0j,2)
        # a+b -> (10+0j,0) + (100+0j,0) = (110+0j,0)
        # c -> (1+0j,3)
        # (110+0j,0) * (1+0j,3) = (110+0j, 3)
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn2, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(110.0, 0), 3) # 110c
        )

        rpn3 = [T('IDENTIFIER', 'a', 1), Token('OPERATOR', '_UMINUS', 0, 1)] # -a
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn3, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(-1.0, 0), 1) # -a
        )

        rpn4 = [T('IDENTIFIER', 'c'), T('FUNCTION', 'log')] # log(c) = log(1000) = 3
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn4, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(3.0, 0), 0)
        )

        rpn5 = [T('IDENTIFIER', 'd'), T('FUNCTION', 'sqrt')] # sqrt(d) = sqrt(10^4) = 10^2 = b
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn5, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(1.0, 0), 2) # b
        )

    def test_evaluate_rpn_complex_numbers(self):
        # Test with #j constant
        rpn_j = [T('CONSTANT_LITERAL', '#j')]
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn_j, self.variables, aop_term_handler.get_term_value, self.base),
            IMAGINARY_UNIT_J # (0+1j, 0)
        )

        # Test 2 * #j
        rpn_2j = [T('NUMBER', '2'), T('CONSTANT_LITERAL', '#j'), T('OPERATOR', '*')]
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn_2j, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(0, 2.0), 0) # (2j, 0)
        )

        # Test #j * #j = -1
        rpn_j_sq = [T('CONSTANT_LITERAL', '#j'), T('CONSTANT_LITERAL', '#j'), T('OPERATOR', '*')]
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn_j_sq, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(-1.0, 0), 0)
        )

        # Test (1 + #j)
        rpn_1_plus_j = [T('NUMBER', '1'), T('CONSTANT_LITERAL', '#j'), T('OPERATOR', '+')]
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn_1_plus_j, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(1.0, 1.0), 0)
        )

        # Test sqrt(-1) -> sqrt(#j*#j) -> #j (principal root)
        # -1 is (complex(-1,0),0)
        # We need to represent -1 as a term. Let's use NUMBER token.
        rpn_sqrt_neg1 = [T('NUMBER', '-1'), T('FUNCTION', 'sqrt')]
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn_sqrt_neg1, self.variables, aop_term_handler.get_term_value, self.base),
            (complex(0, 1), 0) # Should be j
        )

        # Test log(#j) using cmath.log10
        # log10(j) = log10(e^(j*pi/2)) = (j*pi/2) / ln(10) = j * (pi / (2*ln(10)))
        # pi / (2*ln(10)) approx pi / (2*2.3025) approx pi / 4.605 approx 3.14159 / 4.605 approx 0.6821
        expected_log_j = cmath.log10(complex(0,1))
        rpn_log_j = [T('CONSTANT_LITERAL', '#j'), T('FUNCTION', 'log')]
        self.assertValueTupleAlmostEqual(
            aop_parser.evaluate_rpn(rpn_log_j, self.variables, aop_term_handler.get_term_value, self.base),
            (expected_log_j, 0)
        )

    def test_evaluate_rpn_errors(self):
        rpn_bad1 = [T('OPERATOR', '*')]
        with self.assertRaisesRegex(aop_parser.AoPError, "Insufficient operands for operator '\\*'"):
            aop_parser.evaluate_rpn(rpn_bad1, self.variables, aop_term_handler.get_term_value, self.base)

        rpn_bad_stack1 = [T('IDENTIFIER', 'a'), T('IDENTIFIER', 'b')]
        with self.assertRaisesRegex(aop_parser.AoPError, "Invalid RPN evaluation: stack has 2 items at the end."):
            aop_parser.evaluate_rpn(rpn_bad_stack1, self.variables, aop_term_handler.get_term_value, self.base)

if __name__ == '__main__':
    unittest.main()
