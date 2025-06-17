from __future__ import annotations
from typing import Union
import cmath
import decimal # Import the whole module

# Set a higher Emax for Decimal context to handle large exponents like 10^(10^N)
ctx = decimal.getcontext()
ctx.prec = 200
ctx.Emax = decimal.MAX_EMAX
ctx.Emin = decimal.MIN_EMIN

class PracticalLimitError(OverflowError): # Custom error for diagnostics
    """Error raised when an exponent exceeds a practical limit for to_numerical conversion."""
    pass

class AoPValue:
    """
    A recursive class to represent an AoP number.
    Exponent can be a complex number (for float/complex exponents),
    a decimal.Decimal (for precise large integer exponents), or another AoPValue (for recursion).
    """
    def __init__(self, coeff: complex = 1.0, exponent: Union[AoPValue, complex, int, float, decimal.Decimal] = 0.0):
        self.coeff = complex(coeff)

        if isinstance(exponent, AoPValue):
            self.exponent: Union[AoPValue, complex, decimal.Decimal] = exponent
        elif isinstance(exponent, decimal.Decimal):
            if exponent == exponent.to_integral_value():
                self.exponent = exponent
            else:
                self.exponent = complex(float(exponent))
        elif isinstance(exponent, (int, float)):
            if exponent == round(exponent):
                try:
                    self.exponent = decimal.Decimal(int(exponent))
                except OverflowError:
                    self.exponent = complex(exponent)
            else:
                self.exponent = complex(exponent)
        elif isinstance(exponent, complex):
            self.exponent = exponent
        else:
            raise TypeError(f"Unsupported exponent type: {type(exponent)}")

    def is_numeric(self) -> bool:
        """Checks if the value's exponent is a number (complex or Decimal), not another AoPValue."""
        return isinstance(self.exponent, (complex, decimal.Decimal))

    def to_numerical(self, base: int) -> complex:
        """Recursively flattens the AoPValue into a single complex number."""
        if isinstance(self.exponent, AoPValue):
            exponent_numerical = self.exponent.to_numerical(base)
            try:
                return self.coeff * (complex(base) ** exponent_numerical)
            except OverflowError:
                 raise
        elif isinstance(self.exponent, decimal.Decimal):
            PRACTICAL_EXPONENT_LIMIT_FOR_TO_NUMERICAL = decimal.Decimal(300) # Lowered to prevent float overflow
            if self.exponent > PRACTICAL_EXPONENT_LIMIT_FOR_TO_NUMERICAL or \
               self.exponent < -PRACTICAL_EXPONENT_LIMIT_FOR_TO_NUMERICAL:
                raise PracticalLimitError(f"Exponent {self.exponent} exceeds practical limit {PRACTICAL_EXPONENT_LIMIT_FOR_TO_NUMERICAL} in to_numerical.")

            try:
                if self.exponent.is_zero() and self.coeff.imag == 0 and base == 0:
                    if self.coeff == 0: return complex(0)
                    return complex(self.coeff.real)

                num_base = decimal.Decimal(base)
                powered_val = num_base ** self.exponent

                # --- START OF FIX ---
                # The conversion to complex can overflow a standard float. Catch it.
                complex_result = complex(powered_val)
                if cmath.isinf(complex_result.real) or cmath.isinf(complex_result.imag):
                    raise OverflowError(f"Result of {self} with base {base} is too large to represent as a standard float.")
                # --- END OF FIX ---

                return self.coeff * complex_result

            except decimal.Overflow as e_decimal_overflow:
                raise OverflowError(f"Decimal power overflow in to_numerical for {self} with base {base}: {e_decimal_overflow}")
            except OverflowError: # Catch overflow from the complex() conversion
                raise # Re-raise it to be caught by power_value
            except Exception as e:
                raise
        else: # Exponent is complex (standard float based)
            return self.coeff * (complex(base) ** self.exponent)


    def __repr__(self) -> str:
        exp_repr = ""
        if isinstance(self.exponent, decimal.Decimal):
            exp_repr = f"Decimal('{self.exponent}')"
        elif isinstance(self.exponent, complex):
            exp_repr = repr(self.exponent)
        else: # AoPValue
            exp_repr = repr(self.exponent)
        return f"AoPValue(c={repr(self.coeff)}, e={exp_repr})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AoPValue):
            return NotImplemented

        coeffs_close = cmath.isclose(self.coeff, other.coeff)
        if not coeffs_close:
            return False

        s_exp = self.exponent
        o_exp = other.exponent

        if isinstance(s_exp, decimal.Decimal) and isinstance(o_exp, decimal.Decimal):
            return s_exp == o_exp
        elif isinstance(s_exp, decimal.Decimal):
            s_exp = complex(float(s_exp))
        elif isinstance(o_exp, decimal.Decimal):
            o_exp = complex(float(o_exp))

        if isinstance(s_exp, AoPValue) and isinstance(o_exp, AoPValue):
            return s_exp == o_exp
        elif isinstance(s_exp, complex) and isinstance(o_exp, complex):
            return cmath.isclose(s_exp, o_exp)

        return False

    def __hash__(self) -> int:
        exp_hash = 0
        if isinstance(self.exponent, AoPValue):
            exp_hash = hash(self.exponent)
        elif isinstance(self.exponent, decimal.Decimal):
            exp_hash = hash(("Decimal", self.exponent.as_tuple()))
        elif isinstance(self.exponent, complex):
            exp_hash = hash(self.exponent)

        return hash((self.coeff, exp_hash))
