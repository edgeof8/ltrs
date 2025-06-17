# tests/test_aop_formatter.py

import unittest
from src.aopl_python_impl.aop_formatter import format_output
from src.aopl_python_impl.aop_value import AoPValue # Import AoPValue
from src.aopl_python_impl.definitions import OutputFormatMode

class TestAoPFormatter(unittest.TestCase):
    def setUp(self):
        self.base = 10
        # get_letter_func for base 10: a=1, b=2, ..., z=25 (not 26 as in original test)
        # AOP_LETTERS = string.ascii_lowercase[:25] -> a to y
        # EXPONENT_TO_LETTER_MAP: Dict[int, str] = {i + 1: letter for i, letter in enumerate(AOP_LETTERS)}
        # So 'a' is 1, 'y' is 25. 'z' is not part of this default map.
        # The original test used "abcdefghijklmnopqrstuvwxyz"[x-1] which maps 1->a, 26->z.
        # Let's use a map consistent with definitions.py for exponents 1-25.
        self.letter_map = {i + 1: chr(ord('a') + i) for i in range(25)} # a=1, ..., y=25
        self.get_letter_func = lambda x: self.letter_map.get(x, "")
        self.precision = 6

    def test_simple_values(self):
        # format_output(value: AoPValue, base: int, get_letter: LetterGetter, mode: OutputFormatMode, precision: int)
        self.assertEqual(format_output(AoPValue(1.0, 0), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "1")
        self.assertEqual(format_output(AoPValue(0.0, 0), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "0")
        self.assertEqual(format_output(AoPValue(-1.0, 0), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "-1")

    def test_letter_representation(self):
        self.assertEqual(format_output(AoPValue(1.0, 1), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "a")
        self.assertEqual(format_output(AoPValue(1.0, 2), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "b")
        # Max default letter is 'y' for exponent 25
        self.assertEqual(format_output(AoPValue(1.0, 25), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "y")


    def test_large_exponents_no_letter(self):
        # Exponent 26 has no default letter 'z', should format as a^26
        self.assertEqual(format_output(AoPValue(1.0, 26), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "a^26")
        self.assertEqual(format_output(AoPValue(1.0, 100), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "a^100")

    def test_coefficient_with_exponent(self):
        self.assertEqual(format_output(AoPValue(2.0, 1), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "2*a") # Expect 2*a (more concise)
        self.assertEqual(format_output(AoPValue(-2.0, 2), self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "-2*b") # Expect -2*b

    def test_numerical_output(self):
        self.assertEqual(format_output(AoPValue(1.0, 1), self.base, self.get_letter_func, OutputFormatMode.NUMERICAL, self.precision), "10")
        self.assertEqual(format_output(AoPValue(2.0, 1), self.base, self.get_letter_func, OutputFormatMode.NUMERICAL, self.precision), "20")
        # Test with a slightly more complex number
        self.assertEqual(format_output(AoPValue(1.23, 2), self.base, self.get_letter_func, OutputFormatMode.NUMERICAL, self.precision), "123")


    def test_scientific_output(self):
        # format_output does not directly produce "X * 10^Y" for SCIENTIFIC mode.
        # It falls back to numerical or AoP string if overflow.
        # Let's test based on current behavior: numerical for small numbers.
        self.assertEqual(format_output(AoPValue(1.0, 2), self.base, self.get_letter_func, OutputFormatMode.SCIENTIFIC, self.precision), "100")
        self.assertEqual(format_output(AoPValue(2.0, 3), self.base, self.get_letter_func, OutputFormatMode.SCIENTIFIC, self.precision), "2000")
        # If it were to overflow to_numerical, it would become an AoP string
        # e.g. AoPValue(1.0, 1000) in SCIENTIFIC mode would likely be "a^1000"
        # This needs clarification on SCIENTIFIC mode's exact expected output from format_output.
        # For now, testing non-overflow cases.

    def test_recursive_formatting(self):
        # a^(b) -> a^(a^2)
        recursive_val = AoPValue(1.0, AoPValue(1.0, 2)) # a^(a^2)
        self.assertEqual(format_output(recursive_val, self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "a^(b)")

        # 2 * a^(b) -> 2 * a^(a^2)
        recursive_val_coeff = AoPValue(2.0, AoPValue(1.0, 2))
        self.assertEqual(format_output(recursive_val_coeff, self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "2*a^(b)")

        # a^(a^(c)) -> a^(a^(a^3))
        deep_recursive_val = AoPValue(1.0, AoPValue(1.0, AoPValue(1.0, 3)))
        self.assertEqual(format_output(deep_recursive_val, self.base, self.get_letter_func, OutputFormatMode.AOP, self.precision), "a^(a^(c))")

if __name__ == '__main__':
    unittest.main()
