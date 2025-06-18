# aopl_python_impl/aop_value.py
from __future__ import annotations
import cmath, decimal
from typing import List, Union, Optional
from decimal import Decimal

# FIX: REMOVED the self-importing line below
# from .aop_value import AoPValue, AoPTerm, PracticalLimitError

decimal.getcontext().prec = 100
class PracticalLimitError(OverflowError): pass

class AoPValue:
    def __init__(self, terms: Optional[List['AoPTerm']] = None): self.terms: List[AoPTerm] = terms or []
    @classmethod
    def from_number(cls, num: Union[complex, float, int, Decimal]) -> AoPValue: return cls([AoPTerm(coeff=complex(num))])
    @classmethod
    def from_term(cls, term: 'AoPTerm') -> AoPValue: return cls([term])
    def to_numerical(self, base: int) -> complex: return sum(t.to_numerical(base) for t in self.terms)
    def __repr__(self) -> str: return f"AoPValue({self.terms!r})"

class AoPTerm:
    def __init__(self, coeff: complex=1.0, exponent: Union[AoPValue,complex,Decimal,int,float]=0.0):
        self.coeff = complex(coeff)
        self.exponent: Union[AoPValue, complex, Decimal] = Decimal(exponent) if isinstance(exponent, (int,float)) else exponent
    def to_numerical(self, base: int) -> complex:
        exp_val = self.exponent.to_numerical(base) if isinstance(self.exponent, AoPValue) else complex(self.exponent)
        try:
            if cmath.isclose(exp_val.imag, 0): # Real exponent
                real_exp = exp_val.real
                if real_exp > 700: # Adjusted limit, consistent with complex path
                    raise PracticalLimitError("Exponent's real part too large for numerical evaluation.")

                if real_exp == round(real_exp): # If it's a whole number
                    # Use Python's int power for exactness, then convert to Decimal from string
                    try:
                        powered_base_int = pow(base, int(real_exp))
                        # Construct Decimal from string representation of the exact integer
                        return self.coeff * complex(Decimal(str(powered_base_int)))
                    except OverflowError:
                        # This might happen if base^int(real_exp) is too large for standard int->str
                        # or if int(real_exp) is excessively large leading to pow overflow.
                        # Fallback to Decimal power directly.
                        pass
                    except Exception: # Other potential errors with pow or Decimal(str())
                        pass

                # If not a whole number, or if int power path failed/passed through, use Decimal power
                try:
                    # Ensure real_exp is Decimal for Decimal power operation
                    return self.coeff * complex(Decimal(base) ** Decimal(real_exp))
                except (decimal.Overflow, decimal.InvalidOperation, PracticalLimitError):
                    pass # Fall through to the complex power path below

            # If exp_val has a significant imaginary part, or if real Decimal power failed
            # Fallback or standard path for complex exponents
            # Add similar checks for exp_val components for complex power
            if abs(exp_val.real) > 700 or abs(exp_val.imag) > 700:
                 raise PracticalLimitError("Exponent component too large for complex power.")
            result = self.coeff * (complex(base) ** exp_val)
            if not cmath.isfinite(result):
                raise OverflowError("Result of power operation is not finite.")
            return result
        except (OverflowError, PracticalLimitError, ValueError) as e:
            if isinstance(e, PracticalLimitError):
                raise OverflowError(str(e))
            if isinstance(e, ValueError) and "math domain error" in str(e).lower():
                 raise ZeroDivisionError("Invalid power operation (e.g., 0 raised to a negative power).")
            raise OverflowError("Result of power operation is too large or invalid.")
    def __repr__(self) -> str: return f"Term(c={self.coeff!r}, e={self.exponent!r})"
