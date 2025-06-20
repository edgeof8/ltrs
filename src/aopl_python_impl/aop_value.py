# aopl_python_impl/aop_value.py
from __future__ import annotations
import cmath, decimal
from typing import List, Union, Optional, Callable
from decimal import Decimal
from .definitions import OutputFormatMode, PracticalLimitError
# --- THIS IS THE FIX ---
# Remove the broken import. The to_str method was also moved.
# from .aop_formatter import _complex_to_str as fmt_complex, _format_numeric_exponent
# --- END OF FIX ---

decimal.getcontext().prec = 200

class AoPValue:
    def __init__(self, terms: Optional[List['AoPTerm']] = None): self.terms: List[AoPTerm] = terms or []
    @classmethod
    def from_number(cls, num: Union[complex, float, int, Decimal]) -> AoPValue: return cls([AoPTerm(coeff=complex(num), exponent=Decimal('0'))])
    @classmethod
    def from_term(cls, term: 'AoPTerm') -> AoPValue: return cls([term])
    def to_numerical(self, base: int) -> complex:
        # High-precision path for purely real values
        try:
            total_d = Decimal(0)
            for t in self.terms:
                total_d += t.to_decimal(base)
            return complex(total_d)
        except (TypeError, decimal.InvalidOperation, decimal.Overflow):
            # Fallback path for complex numbers
            total_c = complex(0)
            for t in self.terms:
                total_c += t.to_numerical(base) # This will use complex math
            if not cmath.isfinite(total_c):
                raise OverflowError("Sum of terms resulted in non-finite number.")
            return total_c
    def __repr__(self) -> str: return f"AoPValue({self.terms!r})"

    def to_simple_number(self) -> Optional[complex]:
        if len(self.terms) == 1 and self.terms[0].is_numeric_exponent_zero(): return self.terms[0].coeff
        return None

    def to_decimal(self, base: int) -> Decimal:
        """Converts the AoPValue to a Decimal, if possible.
        Raises TypeError if any part is complex.
        """
        if any(not cmath.isclose(t.coeff.imag, 0) for t in self.terms):
            raise TypeError("Cannot convert AoPValue with complex coefficients to Decimal")
        total = Decimal(0)
        for t in self.terms:
            total += t.to_decimal(base)
        return total
    # The to_str method has been removed from here and now lives in aop_formatter.py as format_output

class AoPTerm:
    def __init__(self, coeff: complex=1.0, exponent: Union[AoPValue,complex,Decimal,int,float]=0.0):
        self.coeff = complex(coeff)
        normalized_exponent: Union[AoPValue, complex, Decimal]
        if isinstance(exponent, AoPValue):
            normalized_exponent = exponent
        elif isinstance(exponent, complex):
            if cmath.isclose(exponent.imag, 0):
                # Convert to Decimal and normalize if it's an integer
                d_exp = Decimal(str(exponent.real)) # Convert float to Decimal via string for precision
                # Only quantize if it has a fractional part that is effectively zero (e.g. "3.000")
                # and it's not an already plain integer (like Decimal('200') which has exponent 0)
                # or a very large number where quantize might fail.
                # A Decimal is an integer if its exponent is non-negative after normalization,
                # or if it has a negative exponent but d_exp == d_exp.to_integral_value().
                # Check if the Decimal has a fractional part by examining its exponent
                exp_tuple = d_exp.as_tuple()
                if isinstance(exp_tuple.exponent, int) and exp_tuple.exponent < 0: # Has digits after decimal point (e.g. 3.0, 3.5)
                    if d_exp == d_exp.to_integral_value(rounding=decimal.ROUND_FLOOR): # e.g., 3.0
                        try:
                            normalized_exponent = d_exp.quantize(Decimal('1')) # Attempt to make it Decimal('3')
                        except decimal.InvalidOperation:
                            normalized_exponent = d_exp.to_integral_value(rounding=decimal.ROUND_FLOOR) # Fallback for huge numbers
                    else: # e.g. 3.5
                        normalized_exponent = d_exp
                else:
                    normalized_exponent = d_exp # Already an integer (like Decimal('200')) or has non-zero fraction
            else:
                normalized_exponent = exponent # Keep as complex if imag part is non-zero
        elif isinstance(exponent, (int, float, Decimal)):
            d_exp = Decimal(exponent) # Use direct conversion
            # Check if the Decimal has a fractional part by examining its exponent
            exp_tuple = d_exp.as_tuple()
            if isinstance(exp_tuple.exponent, int) and exp_tuple.exponent < 0: # Has digits after decimal point
                if d_exp == d_exp.to_integral_value(rounding=decimal.ROUND_FLOOR):
                    try:
                        normalized_exponent = d_exp.quantize(Decimal('1'))
                    except decimal.InvalidOperation:
                        normalized_exponent = d_exp.to_integral_value(rounding=decimal.ROUND_FLOOR)
                else:
                    normalized_exponent = d_exp
            else:
                normalized_exponent = d_exp
        else: # Should not be reached if type hints are followed, but as a fallback
            normalized_exponent = exponent
        self.exponent = normalized_exponent
    def is_numeric_exponent_zero(self) -> bool:
        """Checks if the exponent is numerically equal to 0."""
        if isinstance(self.exponent, (int, float, Decimal, complex)):
            try: return cmath.isclose(complex(self.exponent), 0)
            except TypeError: return False
        return False
    def to_numerical(self, base: int) -> complex:
        """Converts the AoPTerm to a complex number, if possible. Raises PracticalLimitError if too large."""
        if isinstance(self.exponent, AoPValue):
            exp_val_complex = self.exponent.to_numerical(base)
        else: exp_val_complex = complex(self.exponent)
        if not cmath.isfinite(exp_val_complex): raise PracticalLimitError("Exponent evaluates to a non-finite number.")
        try:
            # Path for real coefficients and real exponents (use Decimal for precision)
            if cmath.isclose(exp_val_complex.imag, 0, abs_tol=1e-14) and \
               cmath.isclose(self.coeff.imag, 0, abs_tol=1e-14):
                dec_coeff = Decimal(str(self.coeff.real))
                dec_base = Decimal(str(base))
                dec_exp_exponent = Decimal(str(exp_val_complex.real))

                powered_base_dec = dec_base ** dec_exp_exponent # Can raise decimal.Overflow
                result_dec = dec_coeff * powered_base_dec       # Can raise decimal.Overflow

                # Now, convert to complex for the return type, but check for float overflow
                if not result_dec.is_finite(): # e.g. Decimal('NaN'), Decimal('Inf')
                    raise PracticalLimitError(f"Decimal calculation resulted in non-finite value: {result_dec}")

                result_complex = complex(result_dec)
                if not cmath.isfinite(result_complex) and result_dec.is_finite(): # Finite Decimal became non-finite float
                    raise PracticalLimitError(f"Result {result_dec} (finite Decimal) became non-finite when converting to complex for float limits.")
                return result_complex
            else: # Path for complex coefficients or complex exponents
                powered_base = complex(base) ** exp_val_complex
                result_complex = self.coeff * powered_base
                if not cmath.isfinite(result_complex): raise OverflowError("Result is not finite.") # Caught below
                return result_complex
        except (decimal.Overflow, decimal.InvalidOperation, OverflowError) as e: raise PracticalLimitError(f"Numerical evaluation failed: {e}")
    def __repr__(self) -> str: return f"Term(c={self.coeff!r}, e={self.exponent!r})"

    def to_decimal(self, base: int) -> Decimal:
        """Converts the AoPTerm to a Decimal, if possible. Raises TypeError if complex."""
        if not cmath.isclose(self.coeff.imag, 0):
            raise TypeError("Cannot convert term with complex coefficient to Decimal")

        exp_val_d: Decimal
        if isinstance(self.exponent, AoPValue):
            exp_val_d = self.exponent.to_decimal(base)
        elif isinstance(self.exponent, complex):
            if not cmath.isclose(self.exponent.imag, 0): raise TypeError("Cannot convert term with complex exponent to Decimal")
            exp_val_d = Decimal(str(self.exponent.real))
        else:
            exp_val_d = Decimal(str(self.exponent))

        return Decimal(str(self.coeff.real)) * (Decimal(str(base)) ** exp_val_d)
    # The to_str method has been removed from here and now lives in aop_formatter.py as format_term
