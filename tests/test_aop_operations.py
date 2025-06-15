import unittest
import math
import cmath # For complex numbers
from src.aopl_python_impl.definitions import ValueTuple
from src.aopl_python_impl import aop_operations

class TestAoPOperations(unittest.TestCase):

    def assertValueTupleAlmostEqual(self, vt1: ValueTuple, vt2: ValueTuple, places: int = 7, msg: str | None = None, rel_tol=1e-9, abs_tol=0.0):
        """Helper to compare ValueTuples with almost equal for complex coefficients."""
        self.assertIsInstance(vt1, tuple, "First value is not a tuple")
        self.assertIsInstance(vt2, tuple, "Second value is not a tuple")
        self.assertEqual(len(vt1), 2, "First tuple does not have 2 elements")
        self.assertEqual(len(vt2), 2, "Second tuple does not have 2 elements")
        self.assertIsInstance(vt1[0], complex, "First coefficient is not complex")
        self.assertIsInstance(vt2[0], complex, "Second coefficient is not complex")

        coeff_msg = f"{msg if msg is not None else 'ValueTuple comparison failed'} (coefficient mismatch: {vt1[0]} vs {vt2[0]})"
        exp_msg = f"{msg if msg is not None else 'ValueTuple comparison failed'} (exponent mismatch: {vt1[1]} vs {vt2[1]})"

        self.assertTrue(cmath.isclose(vt1[0], vt2[0], rel_tol=rel_tol, abs_tol=abs_tol), msg=coeff_msg)
        self.assertEqual(vt1[1], vt2[1], msg=exp_msg)

    def test_multiply_values(self):
        self.assertValueTupleAlmostEqual(aop_operations.multiply_values((complex(2.0, 0), 3), (complex(5.0, 0), 4)), (complex(10.0, 0), 7))
        self.assertValueTupleAlmostEqual(aop_operations.multiply_values((complex(-2.0, 0), 3), (complex(5.0, 0), 4)), (complex(-10.0, 0), 7))
        self.assertValueTupleAlmostEqual(aop_operations.multiply_values((complex(2.0, 1), 3), (complex(1.0, -2), 4)), (complex(4.0, -3.0), 7))
        self.assertValueTupleAlmostEqual(aop_operations.multiply_values((complex(0, 1), 1), (complex(0, 1), 1)), (complex(-1,0), 2))

    def test_divide_values(self):
        self.assertValueTupleAlmostEqual(aop_operations.divide_values((complex(10.0, 0), 7), (complex(2.0, 0), 3)), (complex(5.0, 0), 4))
        self.assertValueTupleAlmostEqual(aop_operations.divide_values((complex(-10.0, 0), 7), (complex(2.0, 0), 3)), (complex(-5.0, 0), 4))
        self.assertValueTupleAlmostEqual(aop_operations.divide_values((complex(4.0, -3.0), 7), (complex(1.0, -2.0), 4)), (complex(2.0, 1.0), 3))
        with self.assertRaises(ZeroDivisionError):
            aop_operations.divide_values((complex(10.0, 0), 7), (complex(0.0, 0), 3))

    def test_power_value(self):
        base = 10
        self.assertValueTupleAlmostEqual(aop_operations.power_value((complex(2.0, 0), 3), 2.0, base), (complex(4.0, 0), 6)) # (2*10^3)^2 = 4*10^6
        self.assertValueTupleAlmostEqual(aop_operations.power_value((complex(0, 1), 0), 2.0, base), (complex(-1.0,0), 0)) # j^2 = -1
        self.assertValueTupleAlmostEqual(aop_operations.power_value((complex(1,1), 0), 2.0, base), (complex(0,2), 0)) # (1+j)^2 = 2j

        # Test fractional power resulting in integer exponent for base part
        # (4.0 * 10^2)^0.5 = sqrt(400) = 20. Coeff part: 4^0.5=2. Expon part: 2*0.5=1. Result: (2.0, 1)
        self.assertValueTupleAlmostEqual(aop_operations.power_value((complex(4.0, 0), 2), 0.5, base), (complex(2.0, 0), 1))

        # Test fractional power resulting in fractional exponent for base part
        # (2.0 * 10^1)^0.5 = sqrt(20). This should evaluate to (sqrt(20), 0)
        expected_coeff_sqrt20 = cmath.sqrt(20)
        self.assertValueTupleAlmostEqual(
            aop_operations.power_value((complex(2.0,0),1), 0.5, base),
            (expected_coeff_sqrt20, 0)
        )
        # Test (a^0.5) where a is (1,1) base 10. Should be (sqrt(10),0)
        self.assertValueTupleAlmostEqual(
            aop_operations.power_value((complex(1.0,0),1), 0.5, base),
            (cmath.sqrt(10), 0)
        )
        # Test 0^0 = 1
        self.assertValueTupleAlmostEqual(aop_operations.power_value((complex(0,0),0),0.0,base), (complex(1,0),0))
        # Test 0^positive = 0
        self.assertValueTupleAlmostEqual(aop_operations.power_value((complex(0,0),0),2.0,base), (complex(0,0),0))
        # Test 0^negative = Error
        with self.assertRaises(ZeroDivisionError):
            aop_operations.power_value((complex(0,0),0),-2.0,base)


    def test_simplify_value(self):
        base = 10
        self.assertValueTupleAlmostEqual(aop_operations.simplify_value((complex(10.0, 0), 3), base), (complex(1.0, 0), 4))
        self.assertValueTupleAlmostEqual(aop_operations.simplify_value((complex(0.1, 0), 5), base), (complex(1.0, 0), 4))
        self.assertValueTupleAlmostEqual(aop_operations.simplify_value((complex(20.0, 0), 2), base), (complex(20.0, 0), 2))
        self.assertValueTupleAlmostEqual(aop_operations.simplify_value((complex(10.0, 1.0), 3), base), (complex(10.0, 1.0), 3))
        self.assertValueTupleAlmostEqual(aop_operations.simplify_value((complex(0, 10.0), 3), base), (complex(0, 10.0), 3))
        self.assertValueTupleAlmostEqual(aop_operations.simplify_value((complex(10.0, 0), 3), 1), (complex(10.0, 0), 0))

    def test_normalize_value_tuple_for_display(self):
        base = 10
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(123.0, 0), 0), base), (complex(1.23, 0), 2))
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(0.0123, 0), 0), base), (complex(1.23, 0), -2))
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(-123.0, 0), 0), base), (complex(-1.23, 0), 2))
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(100.0, 100.0), 0), base), (complex(1.0, 1.0), 2))
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(0.01, 0.01), 0), base), (complex(1.0, 1.0), -2))
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(1.0, 1.0), 5), base), (complex(1.0, 1.0), 5))
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(10.0, 0), 2), base), (complex(1.0, 0), 3))
        self.assertValueTupleAlmostEqual(aop_operations.normalize_value_tuple_for_display((complex(6.0, 8.0), 0), base), (complex(0.6, 0.8), 1))


if __name__ == '__main__':
    unittest.main()
