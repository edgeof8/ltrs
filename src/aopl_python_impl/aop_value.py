# aopl_python_impl/aop_value.py
from __future__ import annotations
import cmath, decimal
from typing import List, Union, Optional, Callable
from decimal import Decimal
# Import OutputFormatMode and PracticalLimitError from definitions
from .definitions import OutputFormatMode, PracticalLimitError
# Import formatter functions from aop_formatter
from .aop_formatter import _complex_to_str as fmt_complex, _format_numeric_exponent as fmt_num_exp

decimal.getcontext().prec = 100

class AoPValue:
    def __init__(self, terms: Optional[List['AoPTerm']] = None):
        self.terms: List[AoPTerm] = terms or []

    @classmethod
    def from_number(cls, num: Union[complex, float, int, Decimal]) -> AoPValue:
        # This creates an AoPValue representing a number N as N*a^0
        return cls([AoPTerm(coeff=complex(num), exponent=Decimal('0'))]) # Exponent is 0 for numbers

    @classmethod
    def from_term(cls, term: 'AoPTerm') -> AoPValue:
        return cls([term])

    def to_numerical(self, base: int) -> complex:
        total = complex(0)
        try:
            for t in self.terms:
                total += t.to_numerical(base)
        except PracticalLimitError:
            raise
        except OverflowError as e:
            if not cmath.isfinite(total):
                raise OverflowError("Sum of terms resulted in non-finite number.") from e
            raise
        return total


    def __repr__(self) -> str:
        return f"AoPValue({self.terms!r})"

    def to_str(self, base: int, get_letter: Callable, mode: OutputFormatMode, precision: int) -> str:
        # print(f"DEBUG AoPValue.to_str: Value={self!r}, Mode={mode}") # Optional top-level debug
        if not self.terms: return "0"

        if mode in (OutputFormatMode.SCIENTIFIC, OutputFormatMode.NUMERICAL):
            try:
                num = self.to_numerical(base)
                if mode == OutputFormatMode.SCIENTIFIC:
                    return f"{num.real:.{precision}e}" if cmath.isclose(num.imag, 0) else fmt_complex(num, precision)
                else: # NUMERICAL
                    return fmt_complex(num, precision)
            except (OverflowError, PracticalLimitError, NotImplementedError) as e:
                return f"Error: {e}"

        if mode == OutputFormatMode.AUTO and len(self.terms) == 1:
            term = self.terms[0]
            if cmath.isclose(term.coeff, 1.0) and term.is_numeric_real_exponent_in_letter_range():
                exp_int = int(round(complex(term.exponent).real))
                if letter := get_letter(exp_int): # get_letter expects int
                    return letter

            if term.is_numeric_exponent_zero(): # Is it just a number C*a^0?
                return fmt_complex(term.coeff, precision)

        parts = [t.to_str(base, get_letter, precision) for t in self.terms]
        result = parts[0]
        for part in parts[1:]:
            result += f" + {part}" if not part.startswith('-') else f" - {part[1:]}"
        return result

class AoPTerm:
    def __init__(self, coeff: complex=1.0, exponent: Union[AoPValue,complex,Decimal,int,float]=0.0):
        self.coeff = complex(coeff)
        if isinstance(exponent, (int,float)):
            self.exponent: Union[AoPValue, complex, Decimal] = Decimal(exponent)
        elif isinstance(exponent, complex):
            self.exponent = exponent
        else: # AoPValue or Decimal
            self.exponent = exponent

    def is_numeric_exponent_zero(self) -> bool:
        """Checks if the exponent is numerically equivalent to zero."""
        if isinstance(self.exponent, (int, float, Decimal, complex)):
            try:
                return cmath.isclose(complex(self.exponent), 0)
            except TypeError: # Should not happen if type is one of these
                return False
        return False # AoPValue exponent is not considered "numeric zero" by this method

    def is_numeric_real_exponent_in_letter_range(self) -> bool:
        """Checks if exponent is numeric, real, integral, and in range [1,50]."""
        if isinstance(self.exponent, (int, float, Decimal, complex)):
            try:
                exp_comp = complex(self.exponent)
                if cmath.isclose(exp_comp.imag, 0):
                    real_part = exp_comp.real
                    if cmath.isclose(real_part, round(real_part)):
                        exp_int = int(round(real_part))
                        return 1 <= exp_int <= 50
            except TypeError:
                return False
        return False

    def to_numerical(self, base: int) -> complex:
        exp_val: complex
        if isinstance(self.exponent, AoPValue):
            exp_val = self.exponent.to_numerical(base)
        else:
            exp_val = complex(self.exponent)

        try:
            base_val = complex(base)
            powered_base: complex

            if cmath.isclose(exp_val.imag, 0):
                real_exp = exp_val.real
                if real_exp > 308 :
                    raise PracticalLimitError(f"Exponent {real_exp} too large for numerical evaluation.")
                if real_exp < -308 and base != 0:
                    raise PracticalLimitError(f"Exponent {real_exp} too small (negative) for numerical evaluation.")

                # Ensure self.exponent is Decimal if it started as int/float/Decimal for Decimal power
                current_exp_for_power = self.exponent
                if isinstance(current_exp_for_power, complex): # Should only happen if it was originally complex
                    current_exp_for_power = Decimal(current_exp_for_power.real)


                if isinstance(current_exp_for_power, Decimal) and \
                   current_exp_for_power == current_exp_for_power.to_integral_value(rounding=decimal.ROUND_HALF_UP): # Check if it's an integer value
                    try:
                        # Use Decimal for potentially higher precision power with integer exponent
                        # Ensure base is also treated as Decimal if it's an integer for this path
                        base_for_dec_power = Decimal(base) if isinstance(base, int) else Decimal(str(base))
                        powered_base = complex(base_for_dec_power ** current_exp_for_power)
                    except decimal.Overflow:
                        raise PracticalLimitError("Decimal power resulted in overflow.")
                    except decimal.InvalidOperation:
                        powered_base = base_val ** exp_val # Fallback to complex power
                else:
                    powered_base = base_val ** exp_val
            else:
                if abs(exp_val.real) > 300 or abs(exp_val.imag) > 700:
                    raise PracticalLimitError("Exponent component too large for complex power.")
                powered_base = base_val ** exp_val

            if not cmath.isfinite(powered_base):
                raise OverflowError("Result of base exponentiation is not finite.")

            result = self.coeff * powered_base
            if not cmath.isfinite(result):
                raise OverflowError("Final result (coeff * powered_base) is not finite.")
            return result
        except (OverflowError, PracticalLimitError, ValueError, decimal.InvalidOperation) as e:
            if isinstance(e, PracticalLimitError):
                raise
            raise OverflowError(f"Power evaluation failed for term ({self.coeff}*base^{exp_val}): {e}")


    def __repr__(self) -> str:
        return f"Term(c={self.coeff!r}, e={self.exponent!r})"

    def to_str(self, base: int, get_letter: Callable, precision: int) -> str:
        # print(f"DEBUG AoPTerm.to_str: Coeff={self.coeff}, Exponent={self.exponent} (type {type(self.exponent)})") # Keep for now
        coeff_str = fmt_complex(self.coeff, precision)

        if self.is_numeric_exponent_zero():
            # print(f"DEBUG AoPTerm.to_str: Exponent is zero. Returning coeff_str='{coeff_str}'")
            return coeff_str

        exp_str = ""
        if isinstance(self.exponent, AoPValue):
            # print(f"DEBUG AoPTerm.to_str: Exponent is AoPValue. Calling self.exponent.to_str recursively.")
            exp_str = self.exponent.to_str(base, get_letter, OutputFormatMode.AOP, precision)
            # Parenthesize if it's a sum, product, or contains special characters that could cause ambiguity
            if len(self.exponent.terms) > 1 or any(c in exp_str for c in ' *()+^'): # Added ^ to chars list
                exp_str = f"({exp_str})"
        else: # self.exponent is numeric (Decimal, complex, int, float)
            # print(f"DEBUG AoPTerm.to_str: Exponent is numeric ({self.exponent}). Calling fmt_num_exp.")
            exp_str = fmt_num_exp(self.exponent, base, get_letter, precision)
            # print(f"DEBUG AoPTerm.to_str: fmt_num_exp returned '{exp_str}' for exponent {self.exponent}.")

        if coeff_str == "1": return f"a^{exp_str}"
        if coeff_str == "-1": return f"-a^{exp_str}"

        if exp_str.isalnum() or \
           (exp_str.startswith('-') and exp_str[1:].isalnum()) or \
           (exp_str.startswith('+') and exp_str[1:].isalnum()): # Allow + for explicit positive exponents
            return f"{coeff_str}a^{exp_str}"

        return f"{coeff_str}*a^{exp_str}"
