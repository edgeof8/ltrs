# aopl_python_impl/definitions.py
import re, string
from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple, TYPE_CHECKING
from enum import Enum

# --- NEW: Import TYPE_CHECKING for circular dependency avoidance in type hints ---
if TYPE_CHECKING:
    from .aop_value import AoPValue

# --- NEW: Moved from aop_types.py ---
class SymbolicPowerResult:
    """A simple container for an unevaluated power operation."""
    def __init__(self, base: 'AoPValue', exponent: 'AoPValue'):
        self.base = base
        self.exponent = exponent

    def __repr__(self):
        return f"SymbolicPowerResult({self.base!r}^{self.exponent!r})"

    def resolve(self) -> 'AoPValue | SymbolicPowerResult':
        """
        Eagerly evaluates the symbolic power into a final AoPValue.
        This method is now a placeholder; the real logic is in the calculator's
        _resolve_to_value function which provides more context.
        """
        raise NotImplementedError("Direct .resolve() is deprecated. Use the calculator's evaluation pipeline.")


class OutputFormatMode(Enum): AUTO = "auto"; AOP = "aop"; SCIENTIFIC = "sci"; NUMERICAL = "num"
class Token(NamedTuple): kind: str; value: str; start: int; end: int
class AoPError(Exception): pass
class ParseError(AoPError): pass
class EvaluationError(AoPError): pass
class PracticalLimitError(OverflowError): # Specific error for numerical limits
    """Indicates a practical limit was exceeded during numerical evaluation."""
    pass
# --- NEW: Moved from aop_value.py ---
# These helper functions are now centralized to avoid circular imports.
def key_to_int(key: str, base: int = 10) -> int:
    """
    Converts a canonical AoP string exponent (e.g., "b", "Z", "2c5a", "0")
    to its numerical integer value. This Python version is used by the fallback.
    """
    if not key or key == "0": return 0

    total_exp_val = 0
    current_coeff_str = ""

    for char in key:
        if char.isdigit():
            current_coeff_str += char
        elif char.isalpha():
            coeff = int(current_coeff_str) if current_coeff_str else 1
            letter_exp = LETTER_TO_EXPONENT_MAP.get(char, 0)
            total_exp_val += coeff * letter_exp
            current_coeff_str = ""
        else:
            raise ValueError(f"Invalid character in AoP key string: '{key}' (char: '{char}')")

    if current_coeff_str.isnumeric() and not current_coeff_str == "0":
        total_exp_val += int(current_coeff_str)

    return total_exp_val

def int_to_key(exp: int, base: int = 10) -> str:
    """
    Converts a numerical integer exponent to its canonical AoP string representation.
    """
    if exp == 0: return "0"
    parts = []
    remaining_exp = exp
    sorted_exp_values = sorted(LETTER_TO_EXPONENT_MAP.values(), reverse=True)
    sorted_exp_values = list(dict.fromkeys(sorted_exp_values))

    for val in sorted_exp_values:
        if val == 0: continue
        count = remaining_exp // val
        if count > 0:
            letter = EXPONENT_TO_LETTER_MAP.get(val, str(val))
            parts.append(f"{count}{letter}" if count > 1 else str(letter))
            remaining_exp -= count * val

    if remaining_exp > 0:
        parts.append(str(remaining_exp))

    return "".join(parts)

LOWERCASE_AOP_LETTERS = string.ascii_lowercase[0:25]
UPPERCASE_AOP_LETTERS = string.ascii_uppercase[0:25]

# Map of letter to its numerical exponent value (a=1, b=2, ..., y=25, A=26, B=27, ..., Y=50, Z=100)
LETTER_TO_EXPONENT_MAP = {c: i+1 for i, c in enumerate(LOWERCASE_AOP_LETTERS)}
LETTER_TO_EXPONENT_MAP.update({c: i+26 for i, c in enumerate(UPPERCASE_AOP_LETTERS)})
LETTER_TO_EXPONENT_MAP['Z'] = 100
LETTER_TO_EXPONENT_MAP['z'] = 100  # Alias for 'Z'

# Reverse mapping for formatting (1=a, 2=b, ..., 25=y, 26=A, ..., 50=Y, 100=Z)
EXPONENT_TO_LETTER_MAP = {i+1: c for i, c in enumerate(LOWERCASE_AOP_LETTERS)}
EXPONENT_TO_LETTER_MAP.update({i+26: c for i, c in enumerate(UPPERCASE_AOP_LETTERS)})
EXPONENT_TO_LETTER_MAP[100] = 'Z'

# Regular expression for tokenizing input
TOKEN_REGEX: Pattern[str] = re.compile(
    r"(?P<whitespace>\s+)|"
    r"(?P<number>\d+)|"
    r"(?P<identifier>(?:\d*[a-zA-Z])+)|"
    r"(?P<operator>[+\-*/^()])|"
    r"(?P<invalid>.+?)"
)
