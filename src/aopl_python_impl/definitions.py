# aopl_python_impl/definitions.py
import re, string
from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .aop_value import AoPValue

class SymbolicPowerResult:
    def __init__(self, base: Union['AoPValue', 'SymbolicPowerResult'], exponent: Union['AoPValue', 'SymbolicPowerResult']):
        self.base = base
        self.exponent = exponent

    @property
    def ultimate_base_aop_value(self) -> 'AoPValue':
        """Recursively finds the root AoPValue base of the nested power structure."""
        current_base = self.base
        while isinstance(current_base, SymbolicPowerResult):
            current_base = current_base.base
        return current_base

    def __repr__(self):
        return f"SymbolicPowerResult({self.base!r}^{self.exponent!r})"
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
            root_aop_base = self.ultimate_base_aop_value
            one = AoPValue.from_number(1, base=root_aop_base.base)
            new_exponent = self.exponent + one
            return SymbolicPowerResult(self.base, new_exponent)
        return NotImplemented
    def __rmul__(self, other):
        return self.__mul__(other)

# --- THIS IS THE FIX ---
class Token(NamedTuple):
    kind: str
    value: str
    start: int
    end: int

class AoPError(Exception): pass

# ... (rest of the file is correct)
LOWERCASE_AOP_LETTERS = string.ascii_lowercase[:25]
UPPERCASE_AOP_LETTERS = string.ascii_uppercase[:25]
LETTER_TO_EXPONENT_MAP = {c: i+1 for i, c in enumerate(LOWERCASE_AOP_LETTERS)}
LETTER_TO_EXPONENT_MAP.update({c: i+26 for i, c in enumerate(UPPERCASE_AOP_LETTERS)})
LETTER_TO_EXPONENT_MAP['Z'] = 100
LETTER_TO_EXPONENT_MAP['z'] = 100
EXPONENT_TO_LETTER_MAP = {v: k for k, v in LETTER_TO_EXPONENT_MAP.items() if k != 'z'}
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


def key_to_int(key_str: str, _base: int = 10) -> int:
    """
    Converts a canonical AoP string exponent (e.g., "b", "Z", "2c5a", "0")
    to its numerical integer value.
    """
    if key_str == "0":  # Canonical string for exponent 0
        return 0

    total_exp_val = 0
    current_coeff_str = ""
    current_letter_str = ""

    # Iterate through the string to parse it
    for char in key_str:
        if char.isdigit():
            current_coeff_str += char
        elif char.isalpha():
            # Process the previous coeff/letter group (if any)
            if not current_coeff_str.isnumeric() and not current_letter_str.isalpha():
                # This handles cases like "b" or "Z" where there's no explicit coeff
                coeff = 1
            elif current_coeff_str.isnumeric():
                coeff = int(current_coeff_str)
            else:
                raise ValueError(f"Invalid AoP key format: '{key_str}'. Expected digit or letter, got '{char}' after non-coeff.")

            current_letter_exp = LETTER_TO_EXPONENT_MAP.get(char, 0)
            total_exp_val += coeff * current_letter_exp

            current_coeff_str = ""  # Reset for next group
            current_letter_str = ""  # Reset
        else:
            raise ValueError(f"Invalid character in AoP key string: '{key_str}' (char: '{char}')")

    # Handle cases like "5" (a standalone number exponent)
    if current_coeff_str.isnumeric() and not current_letter_str.isalpha():
        total_exp_val += int(current_coeff_str)  # Assume it's 5 * 10^0

    return total_exp_val


def int_to_key(exp_num: int, _base: int = 10) -> str:
    """
    Converts a numerical integer exponent to its canonical AoP string representation.
    e.g., 1 -> "a", 2 -> "b", 26 -> "A", 100 -> "Z", 101 -> "Za" (or aZ based on canonical form)
    """
    if exp_num == 0:
        return "0"  # Canonical string for exponent 0

    parts = []
    remaining_exp = exp_num

    # Iterate through possible exponent values from highest to lowest
    sorted_exp_values = sorted(LETTER_TO_EXPONENT_MAP.values(), reverse=True)
    sorted_exp_values = list(dict.fromkeys(sorted_exp_values))  # Remove duplicates if 'z' and 'Z' both map to 100

    for val in sorted_exp_values:
        if val == 0: continue  # Skip 0, handled by "0" return
        if remaining_exp == 0: break

        count = remaining_exp // val
        if count > 0:
            letter = EXPONENT_TO_LETTER_MAP.get(val, f"({val})")
            term = f"{count}*{letter}" if count > 1 else letter
            parts.append(term)
            remaining_exp -= count * val

    if remaining_exp > 0:
        parts.append(str(remaining_exp))

    # Join with '+' for multiplication of terms in the exponent, not concatenation
    return " + ".join(parts)
