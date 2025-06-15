import unittest
import math
import cmath # For complex numbers
from src.aopl_python_impl.definitions import ValueTuple, IMAGINARY_UNIT_J
from src.aopl_python_impl import aop_term_handler

class TestAoPTermHandler(unittest.TestCase):

    def setUp(self):
        self.variables: dict[str, ValueTuple] = {}

    def assertValueTupleAlmostEqual(self, vt1: ValueTuple, vt2: ValueTuple, places: int = 7, msg: str | None = None, rel_tol=1e-9, abs_tol=0.0):
        """Helper to compare ValueTuples with almost equal for complex coefficients."""
        self.assertIsInstance(vt1, tuple, "First value is not a tuple")
        self.assertIsInstance(vt2, tuple, "Second value is not a tuple")
        self.assertEqual(len(vt1), 2, "First tuple does not have 2 elements")
        self.assertEqual(len(vt2), 2, "Second tuple does not have 2 elements")
        self.assertIsInstance(vt1[0], complex, f"First coefficient is not complex: {vt1[0]}")
        self.assertIsInstance(vt2[0], complex, f"Second coefficient is not complex: {vt2[0]}")

        coeff_msg = f"{msg if msg is not None else 'ValueTuple comparison failed'} (coefficient mismatch: {vt1[0]} vs {vt2[0]})"
        exp_msg = f"{msg if msg is not None else 'ValueTuple comparison failed'} (exponent mismatch: {vt1[1]} vs {vt2[1]})"

        self.assertTrue(cmath.isclose(vt1[0], vt2[0], rel_tol=rel_tol, abs_tol=abs_tol), msg=coeff_msg)
        self.assertEqual(vt1[1], vt2[1], msg=exp_msg)

    def test_get_exponent(self):
        self.assertEqual(aop_term_handler.get_exponent('a'), 1)
        self.assertEqual(aop_term_handler.get_exponent('@'), 0)
        self.assertEqual(aop_term_handler.get_exponent(''), 0)

    def test_get_letter_for_exponent(self):
        self.assertEqual(aop_term_handler.get_letter_for_exponent(1), 'a')
        self.assertIsNone(aop_term_handler.get_letter_for_exponent(0))
        self.assertIsNone(aop_term_handler.get_letter_for_exponent(27))

    def test_calculate_word_exponent(self):
        self.assertEqual(aop_term_handler.calculate_word_exponent("cat"), 24)
        self.assertEqual(aop_term_handler.calculate_word_exponent("C@T"), 23) # Non-alpha ignored
        self.assertEqual(aop_term_handler.calculate_word_exponent(""), 0)

    def test_get_term_value(self):
        # Test kind='IDENTIFIER' (words become complex(1.0,0) coeff)
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("a", self.variables, kind='IDENTIFIER'), (complex(1.0, 0), 1))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("cat", self.variables, kind='IDENTIFIER'), (complex(1.0, 0), 24))

        # Test variable lookup (variables will store complex coeffs)
        self.variables["my_var_test"] = (complex(2.0, 1.0), 5) # (2+j, 5)
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("my_var_test", self.variables, kind='IDENTIFIER'), (complex(2.0, 1.0), 5))
        del self.variables["my_var_test"]
        with self.assertRaisesRegex(ValueError, "Undefined variable or invalid word structure: 'undefined_var'"):
            aop_term_handler.get_term_value("undefined_var", self.variables, kind='IDENTIFIER')

        # Test kind='NUMBER' (becomes complex(float, 0))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("123", self.variables, kind='NUMBER'), (complex(123.0, 0), 0))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("-2.5", self.variables, kind='NUMBER'), (complex(-2.5, 0), 0))

        # Test kind='COEFF_WORD' (coeff becomes complex(float,0))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("2.5cat", self.variables, kind='COEFF_WORD'), (complex(2.5, 0), 24))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("-2b", self.variables, kind='COEFF_WORD'), (complex(-2.0, 0), 2))

        # Test kind='UNITY'
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("Unity(1)", self.variables, kind='UNITY'), (complex(1.0, 0), 0))

        # Test kind='CONSTANT_LITERAL'
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("#pi", self.variables, kind='CONSTANT_LITERAL'), (complex(math.pi, 0), 0))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("π", self.variables, kind='CONSTANT_LITERAL'), (complex(math.pi, 0), 0))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("#e", self.variables, kind='CONSTANT_LITERAL'), (complex(math.e, 0), 0))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("#j", self.variables, kind='CONSTANT_LITERAL'), IMAGINARY_UNIT_J) # (0+1j, 0)

        with self.assertRaisesRegex(ValueError, "Unknown or malformed CONSTANT_LITERAL"):
            aop_term_handler.get_term_value("#unknown", self.variables, kind='CONSTANT_LITERAL')

        # Test fallback (kind=None) for an invalid term
        with self.assertRaisesRegex(ValueError, "Invalid term format, cannot parse: '@'"):
            aop_term_handler.get_term_value("@", self.variables)

        # Test fallback (kind=None) for valid terms (should delegate to kind-specific)
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("123", self.variables), (complex(123.0, 0), 0))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("dog", self.variables), (complex(1.0, 0), 26))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("3z", self.variables), (complex(3.0, 0), 26))
        self.assertValueTupleAlmostEqual(aop_term_handler.get_term_value("#p", self.variables), (complex(math.pi, 0), 0)) # #p normalizes to #pi

if __name__ == '__main__':
    unittest.main()
