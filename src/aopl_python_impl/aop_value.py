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

        # Try to simplify to a single number first for formatting
        try:
            # This is a non-mutating simplification for display purposes only
            num_val = self.to_numerical(base)
            return _format_numeric_exponent(num_val, base, get_letter, precision)
        except (PracticalLimitError, OverflowError, NotImplementedError):
            # Cannot be represented as a single number, so format symbolically.
            pass

        # FIX: Correctly build the string term-by-term
        parts = []
        for t in self.terms:
            part_str = t.to_str(base, get_letter, mode, precision)
            # AoPTerm.to_str will now handle its own sign for subsequent terms
            parts.append(part_str)

        # Join the parts, minding the signs
        result = parts[0]
        for part in parts[1:]:
            if part.startswith('-'):
                result += f" - {part[1:]}"
            else:
                result += f" + {part}"
        return result

    def __repr__(self) -> str:
        return f"AoPValue({self.terms!r})"

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
        # If term represents a pure number (C*a^0), format the number C.
        if self.is_numeric_exponent_zero():
             return _format_numeric_exponent(self.coeff, base, get_letter, precision)

        # FIX: Streamlined and corrected string construction logic.

        # Part 1: Coefficient String
        coeff_part = ""
        if cmath.isclose(self.coeff, 1.0):
            coeff_part = "" # No "1" for 1*a^k
        elif cmath.isclose(self.coeff, -1.0):
            coeff_part = "-" # Just a minus sign for -1*a^k
        else:
            # Format the coefficient. If it's complex, it will include parentheses.
            coeff_part = _format_numeric_exponent(self.coeff, base, get_letter, precision)

        # Part 2: Exponent String
        exp_part = ""
        if isinstance(self.exponent, AoPValue):
            # Recursively format the exponent. Add parens if it's a sum.
            raw_exp_str = self.exponent.to_str(base, get_letter, OutputFormatMode.AOP, precision)
            if len(self.exponent.terms) > 1:
                exp_part = f"({raw_exp_str})"
            else:
                exp_part = raw_exp_str
        else:
            # For numeric exponents, format them. _format_numeric_exponent is smart enough now.
            exp_part = _format_numeric_exponent(self.exponent, base, get_letter, precision)

        # Part 3: Combine them
        # Handle special cases like a^1 -> a
        if exp_part == "1":
            base_str = "a"
        else:
            base_str = f"a^{exp_part}"

        if not coeff_part: # Coeff is 1
            return base_str
        if coeff_part == "-": # Coeff is -1
            return f"-{base_str}"

        # Check if we need an explicit multiplication sign
        # No sign needed if coeff is a number and base_str starts with a letter, e.g., "2a"
        if (coeff_part.replace('.', '', 1).replace('-', '', 1).isdigit() and base_str.startswith('a')):
             return f"{coeff_part}{base_str}"

        return f"{coeff_part}*{base_str}"
