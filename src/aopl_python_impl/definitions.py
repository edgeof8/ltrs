# aopl_python_impl/definitions.py

# Mapping of exponents to their corresponding letter representations
EXPONENT_TO_LETTER_MAP = {
    0: "0",
    1: "a",
    2: "b",
    3: "c",
    4: "d",
    5: "e",
    6: "f",
    7: "g",
    8: "h",
    9: "i",
    10: "j",
    20: "k",
    30: "l",
    40: "m",
    50: "n",
    60: "o",
    70: "p",
    80: "q",
    90: "r",
    100: "Z",
}

# Reverse mapping of letters to exponents
LETTER_TO_EXPONENT_MAP = {v: k for k, v in EXPONENT_TO_LETTER_MAP.items()}

# Token class for parsing
class Token:
    def __init__(self, kind, value=None):
        self.kind = kind
        self.value = value

    # Token type constants
    NUMBER = "NUMBER"
    LETTER = "LETTER"
    OPERATOR = "OPERATOR"
    POWER = "POWER"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"

# Regular expression for tokenizing input
TOKEN_REGEX = r'(\d+|[a-zA-Z]+|[+\-*/^()]|\s+)'

# Custom exception for AoP errors
class AoPError(Exception):
    pass

# Class to represent symbolic power results
class SymbolicPowerResult:
    def __init__(self, base, exponent):
        self.base = base
        self.exponent = exponent

def int_to_key(exp: int, base: int = 10) -> str:
    """
    Converts a numerical integer exponent to its canonical AoP string representation.
    """
    if exp == 0: return "0"

    # Direct lookup for simple cases
    if exp in EXPONENT_TO_LETTER_MAP:
        return EXPONENT_TO_LETTER_MAP[exp]

    parts = []
    remaining_exp = exp
    # Sort by value, descending, to build the string greedily (e.g., Z before a)
    sorted_exp_values = sorted(LETTER_TO_EXPONENT_MAP.values(), reverse=True)
    # Remove duplicates if z and Z map to the same value
    sorted_exp_values = list(dict.fromkeys(sorted_exp_values))

    for val in sorted_exp_values:
        if val == 0: continue
        if remaining_exp >= val:
            count = remaining_exp // val
            if count > 0:
                letter = EXPONENT_TO_LETTER_MAP.get(val, str(val))
                # Append count only if it's greater than 1
                parts.append(f"{count}{letter}" if count > 1 else str(letter))
                remaining_exp -= count * val

    if remaining_exp > 0:
        parts.append(str(remaining_exp))

    # --- FIX: Join with '*' for multiplication, not '+' ---
    return "*".join(parts)
