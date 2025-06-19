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
        if isinstance(exponent, (int,float)): self.exponent: Union[AoPValue, complex, Decimal] = Decimal(str(exponent))
        elif isinstance(exponent, complex): self.exponent = exponent
        else: self.exponent = exponent
    def is_numeric_exponent_zero(self) -> bool:
        """Checks if the exponent is numerically equal to 0."""
        if isinstance(self.exponent, (int, float, Decimal, complex)):
            try: return cmath.isclose(complex(self.exponent), 0)
            except TypeError: return False
        return False
    def to_numerical(self, base: int) -> complex:
        if cmath.isclose(self.coeff, 0): return complex(0)
        exp_val_complex: complex
        if isinstance(self.exponent, AoPValue): exp_val_complex = self.exponent.to_numerical(base)
        else: exp_val_complex = complex(self.exponent)
        if not cmath.isfinite(exp_val_complex): raise PracticalLimitError("Exponent evaluates to a non-finite number.")
        try:
            if cmath.isclose(exp_val_complex.imag, 0) and cmath.isclose(self.coeff.imag, 0):
                return complex(Decimal(str(self.coeff.real)) * (Decimal(str(base)) ** Decimal(str(exp_val_complex.real))))
            powered_base = complex(base) ** exp_val_complex
            result = self.coeff * powered_base
            if not cmath.isfinite(result): raise OverflowError("Result is not finite.")
            return result
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
