# aopl_python_impl/aop_value.py
from __future__ import annotations
import cmath, decimal, logging
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
        original_exponent_repr = repr(exponent) # For logging
        normalized_exponent: Union[AoPValue, complex, Decimal]
        if isinstance(exponent, AoPValue):
            normalized_exponent = exponent
        elif isinstance(exponent, complex):
            if cmath.isclose(exponent.imag, 0):
                # Convert to Decimal and normalize if it's an integer
                d_exp = Decimal(str(exponent.real)) # Convert float to Decimal via string for precision
                # Check if it has a zero fractional part without using quantize on huge numbers
                if d_exp % 1 == 0: # This is a robust way to check for integer value
                    # Store as integer Decimal by converting to int first, avoids quantize issues
                    normalized_exponent = Decimal(int(d_exp))
                else:
                    normalized_exponent = d_exp
            else:
                normalized_exponent = exponent # Keep as complex if imag part is non-zero
        elif isinstance(exponent, (int, float, Decimal)):
            d_exp = Decimal(exponent) # Use direct conversion
            # Check if it has a zero fractional part
            if d_exp % 1 == 0:
                # For very large floats like 2E200, int() might fail. Use to_integral_value.
                try:
                    # This is the safest way to get the integer value without overflow
                    normalized_exponent = d_exp.to_integral_value(rounding=decimal.ROUND_FLOOR)
                except decimal.InvalidOperation: # Can happen for very large numbers
                    normalized_exponent = d_exp # Keep as is if conversion fails
            else:
                normalized_exponent = d_exp
        else: # Should not be reached if type hints are followed, but as a fallback
            normalized_exponent = exponent
        self.exponent = normalized_exponent
        if repr(self.exponent) != original_exponent_repr:
            logging.debug(f"AoPTerm.__init__: exponent normalized from {original_exponent_repr} to {repr(self.exponent)}")
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

                powered_base_dec = dec_base ** dec_exp_exponent
                result_dec = dec_coeff * powered_base_dec

                if not result_dec.is_finite():
                    raise PracticalLimitError(f"Decimal calculation resulted in non-finite value: {result_dec}")

                result_complex = complex(result_dec)
                return result_complex
            else: # Path for complex coefficients or complex exponents
                powered_base = complex(base) ** exp_val_complex
                result_complex = self.coeff * powered_base
                if not cmath.isfinite(result_complex): raise OverflowError("Result is not finite.")
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
