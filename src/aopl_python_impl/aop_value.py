# aopl_python_impl/aop_value.py
from __future__ import annotations
import cmath, decimal
from typing import List, Union, Optional
from decimal import Decimal

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
            if cmath.isclose(exp_val.imag, 0):
                if exp_val.real > 300: raise PracticalLimitError()
                return self.coeff * complex(Decimal(base) ** Decimal(exp_val.real))
        except (decimal.Overflow, PracticalLimitError): raise OverflowError()
        return self.coeff * (complex(base) ** exp_val)
    def __repr__(self) -> str: return f"Term(c={self.coeff!r}, e={self.exponent!r})"
