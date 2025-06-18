# aopl_python_impl/aop_value.py
from __future__ import annotations
import cmath, decimal
from typing import List, Union, Optional, Callable
from decimal import Decimal
from .definitions import OutputFormatMode, PracticalLimitError
from .aop_formatter import _complex_to_str as fmt_complex, _format_numeric_exponent

decimal.getcontext().prec = 100

class AoPValue:
    def __init__(self, terms: Optional[List['AoPTerm']] = None):
        self.terms: List[AoPTerm] = terms or []

    @classmethod
    def from_number(cls, num: Union[complex, float, int, Decimal]) -> AoPValue:
        return cls([AoPTerm(coeff=complex(num), exponent=Decimal('0'))])

    @classmethod
    def from_term(cls, term: 'AoPTerm') -> AoPValue:
        return cls([term])

    def to_numerical(self, base: int) -> complex:
        total = complex(0)
        for t in self.terms:
            total += t.to_numerical(base)
        if not cmath.isfinite(total):
            raise OverflowError("Sum of terms resulted in non-finite number.")
        return total

    def to_str(self, base: int, get_letter: Callable, mode: OutputFormatMode, precision: int) -> str:
        if not self.terms: return "0"

        if len(self.terms) == 1:
            return self.terms[0].to_str(base, get_letter, mode, precision)

        parts = [t.to_str(base, get_letter, mode, precision) for t in self.terms]
        result = parts[0]
        for part in parts[1:]:
            if part.startswith('-'):
                result += f" - {part[1:]}"
            else:
                result += f" + {part}"
        return result

    def __repr__(self) -> str:
        return f"AoPValue({self.terms!r})"

    def to_simple_number(self) -> Optional[complex]:
        """If the value represents a single number (coeff * base^0), return it. Otherwise None."""
        if len(self.terms) == 1 and self.terms[0].is_numeric_exponent_zero():
            return self.terms[0].coeff
        return None

# aopl_python_impl/aop_value.py -> AoPTerm class

class AoPTerm:
    def __init__(self, coeff: complex=1.0, exponent: Union[AoPValue,complex,Decimal,int,float]=0.0):
        self.coeff = complex(coeff)
        if isinstance(exponent, (int,float)):
            self.exponent: Union[AoPValue, complex, Decimal] = Decimal(str(exponent))
        elif isinstance(exponent, complex):
            self.exponent = exponent
        else: self.exponent = exponent

    def is_numeric_exponent_zero(self) -> bool:
        if isinstance(self.exponent, (int, float, Decimal, complex)):
            try: return cmath.isclose(complex(self.exponent), 0)
            except TypeError: return False
        return False

    def to_numerical(self, base: int) -> complex:
        exp_val_complex: complex
        if isinstance(self.exponent, AoPValue):
            exp_val_complex = self.exponent.to_numerical(base)
        else: exp_val_complex = complex(self.exponent)

        if not cmath.isfinite(exp_val_complex):
            raise PracticalLimitError("Exponent evaluates to a non-finite number.")

        try:
            if cmath.isclose(exp_val_complex.imag, 0) and cmath.isclose(self.coeff.imag, 0):
                exp_dec = Decimal(str(exp_val_complex.real))
                coeff_dec = Decimal(str(self.coeff.real))
                base_dec = Decimal(str(base))
                result_dec = coeff_dec * (base_dec ** exp_dec)
                return complex(result_dec)
            elif cmath.isclose(exp_val_complex.imag, 0):
                exp_dec = Decimal(str(exp_val_complex.real))
                base_dec = Decimal(str(base))
                powered_base_dec = base_dec ** exp_dec
                return self.coeff * complex(powered_base_dec)
            else:
                if abs(exp_val_complex.real) > 700 or abs(exp_val_complex.imag) > 700:
                    raise PracticalLimitError("Exponent component too large for complex power.")
                powered_base = complex(base) ** exp_val_complex
                result = self.coeff * powered_base
                if not cmath.isfinite(result): raise OverflowError("Result is not finite.")
                return result
        except (decimal.Overflow, decimal.InvalidOperation, OverflowError) as e:
            raise PracticalLimitError(f"Numerical evaluation failed: {e}")

    def __repr__(self) -> str:
        return f"Term(c={self.coeff!r}, e={self.exponent!r})"

    def to_str(self, base: int, get_letter: Callable, mode: OutputFormatMode, precision: int) -> str:
        # Case 1: The term itself simplifies to a single letter (e.g., 1*a^6 -> f)
        if cmath.isclose(self.coeff, 1.0) and not isinstance(self.exponent, AoPValue):
            try:
                exp_num = complex(self.exponent)
                if cmath.isclose(exp_num.imag, 0) and cmath.isclose(exp_num.real, round(exp_num.real)):
                    exp_int = int(round(exp_num.real))
                    if letter := get_letter(exp_int):
                        return letter
            except (TypeError, ValueError):
                pass

        # Case 2: The term is a simple number (e.g., from 3+5=8 or 2*a^0)
        if self.is_numeric_exponent_zero():
             return _format_numeric_exponent(self.coeff, base, get_letter, precision)

        # Case 3: Format as a full C*a^E expression
        coeff_part = ""
        if cmath.isclose(self.coeff, 1.0): coeff_part = ""
        elif cmath.isclose(self.coeff, -1.0): coeff_part = "-"
        else: coeff_part = _format_numeric_exponent(self.coeff, base, get_letter, precision)

        exp_part = ""
        if isinstance(self.exponent, AoPValue):
            raw_exp_str = self.exponent.to_str(base, get_letter, OutputFormatMode.AOP, precision)
            exp_part = f"({raw_exp_str})" if ' + ' in raw_exp_str or ' - ' in raw_exp_str else raw_exp_str
        else:
            # FIX: Exponents are ALWAYS formatted as numbers, never letters.
            # Pass a lambda that always returns None for the get_letter function.
            exp_part = _format_numeric_exponent(self.exponent, base, lambda x: None, precision)

        base_str = f"a^{exp_part}" if exp_part != "1" else "a"

        if not coeff_part: return base_str
        if coeff_part == "-": return f"-{base_str}"

        # Determine if a '*' is needed
        if coeff_part.replace('.', '', 1).replace('-', '', 1).isdigit() and base_str.startswith('a'):
            return f"{coeff_part}{base_str}"

        return f"{coeff_part}*{base_str}"
