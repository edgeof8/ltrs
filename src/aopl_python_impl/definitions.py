# aopl_python_impl/definitions.py
import re, string
from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .aop_value import AoPValue

class SymbolicPowerResult:
    """A simple container for a lazy, unevaluated power operation."""
    def __init__(self, base: Union['AoPValue', 'SymbolicPowerResult'], exponent: Union['AoPValue', 'SymbolicPowerResult']):
        self.base = base
        self.exponent = exponent

    def __repr__(self):
        return f"SymbolicPowerResult({self.base!r}^{self.exponent!r})"

    @property
    def system_base(self) -> int:
        """Recursively finds the integer base of the entire symbolic power expression."""
        # This helper is needed because self.base can be another SymbolicPowerResult.
        current = self.base
        while isinstance(current, SymbolicPowerResult):
            current = current.base
        # At the end of the chain, current is guaranteed to be an AoPValue.
        return current.base

    def __add__(self, other):
        return NotImplemented

    def __radd__(self, other):
        return NotImplemented

    def __mul__(self, other):
        from .aop_value import AoPValue

        if isinstance(other, SymbolicPowerResult) and self.base == other.base:
            new_exponent = self.exponent + other.exponent
            return SymbolicPowerResult(self.base, new_exponent)

        if isinstance(other, AoPValue) and self.base == other:
            # Use the new helper property to safely get the integer base.
            one = AoPValue.from_number(1, base=self.system_base)
            new_exponent = self.exponent + one
            return SymbolicPowerResult(self.base, new_exponent)

        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)


class Token(NamedTuple): kind: str; value: str; start: int; end: int
class AoPError(Exception): pass

LOWERCASE_AOP_LETTERS = string.ascii_lowercase[:25]
UPPERCASE_AOP_LETTERS = string.ascii_uppercase[:25]
LETTER_TO_EXPONENT_MAP = {c: i+1 for i, c in enumerate(LOWERCASE_AOP_LETTERS)}
LETTER_TO_EXPONENT_MAP.update({c: i+26 for i, c in enumerate(UPPERCASE_AOP_LETTERS)})
LETTER_TO_EXPONENT_MAP['Z'] = 100
LETTER_TO_EXPONENT_MAP['z'] = 100
EXPONENT_TO_LETTER_MAP = {v: k for k, v in LETTER_TO_EXPONENT_MAP.items() if k != 'z'}

def int_to_key(exp: int, base: int) -> str:
    """Converts an integer exponent to a string representation using letter mapping."""
    if exp in EXPONENT_TO_LETTER_MAP:
        return EXPONENT_TO_LETTER_MAP[exp]
    elif exp == 0:
        return ""
    else:
        return f"{exp}"

TOKEN_REGEX = re.compile(r"(\*\*|==|[+\-*/^()])")
OPERATORS = {
    '=': {'precedence': 1, 'associativity': 'right'},
    '==': {'precedence': 1.5, 'associativity': 'left'},
    '+': {'precedence': 2, 'associativity': 'left'},
    '-': {'precedence': 2, 'associativity': 'left'},
    '*': {'precedence': 3, 'associativity': 'left'},
    '/': {'precedence': 3, 'associativity': 'left'},
    '^': {'precedence': 5, 'associativity': 'right'},
    '**': {'precedence': 5, 'associativity': 'right'}
}
