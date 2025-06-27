# aopl_python_impl/definitions.py
import re, string
from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple
from enum import Enum

class OutputFormatMode(Enum): AUTO = "auto"; AOP = "aop"; SCIENTIFIC = "sci"; NUMERICAL = "num"
class Token(NamedTuple): kind: str; value: str; start: int; end: int

class AoPError(ValueError): # General parsing/evaluation error
    def __init__(self, message: str, token: Optional[Token] = None):
        self.message, self.token = message, token
        super().__init__(message)

class PracticalLimitError(OverflowError): # Specific error for numerical limits
    """Indicates a practical limit was exceeded during numerical evaluation."""
    pass

# FIX: Removed unused ValueTuple, which was a remnant from an older design.
# This cleans up the definitions and removes obsolete code.

LOWERCASE_AOP_LETTERS = string.ascii_lowercase[:25] # a-y
UPPERCASE_AOP_LETTERS_STD = string.ascii_uppercase[:25] # A-Y (exponents 26-50)

_letter_map_builder = {l: i + 1 for i, l in enumerate(LOWERCASE_AOP_LETTERS)} # a-y: 1-25
_letter_map_builder.update({l: i + 26 for i, l in enumerate(UPPERCASE_AOP_LETTERS_STD)}) # A-Y: 26-50
_letter_map_builder['Z'] = 100 # Uppercase Z for base^100
_letter_map_builder['z'] = 100 # Lowercase z as alias for Z, also base^100

LETTER_TO_EXPONENT_MAP: Dict[str, int] = _letter_map_builder
EXPONENT_TO_LETTER_MAP: Dict[int, str] = {v: k for k, v in LETTER_TO_EXPONENT_MAP.items()}

_opt_sign = r"[+-]?"
_number_bare = r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?"
_integer_bare = r"\d+"
_any_number = f"(?:{_number_bare}|{_integer_bare})"
_number_signed = f"{_opt_sign}{_any_number}"
_word_simple = r"[a-yA-YzZ]+" # Ensures 'a'-'y', 'A'-'Y', 'z', 'Z' are matched by IDENTIFIER/COEFF_WORD
_variable_name = r"\$[a-zA-Z_]\w*" # Assuming variables are GUI-only or distinct from AoP letters
_constants = r'#pi|#e|#phi|#tau|#sqrt2|#j|#sqrt3|#ln2' # Added new constants

TOKEN_SPECIFICATION: List[Tuple[str, str]] = [
    # Operators first to ensure they are captured before numbers/coeff_words that might start with + or -
    # Added '=='
    ('OPERATOR', r"\*\*|==|[\+\-\*\/\^=]"), # Could also add !=, <=, >=, <, > later
    ('VARIABLE', _variable_name),
    # --- FIX: Removed the greedy COEFF_WORD token. This is the core fix. ---
    # Now, '2a' will be tokenized as a NUMBER '2' followed by an IDENTIFIER 'a',
    # allowing implicit multiplication to be handled correctly.
    # ('COEFF_WORD', f"{_number_signed}{_word_simple}"),
    ('CONSTANT_LITERAL', _constants),
    ('NUMBER', _number_signed),
    ('IDENTIFIER', _word_simple),
    ('LPAREN', r"\("), ('RPAREN', r"\)"),
    ('WHITESPACE', r"\s+"), ('MISMATCH', r"."),
]
TOKEN_REGEX: Pattern[str] = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))
OPERATORS: Dict[str, Dict] = {
    '=': {'precedence': 1, 'associativity': 'right'}, # Assignment (if ever used as an operator)
    '==': {'precedence': 1.5, 'associativity': 'left'}, # Equality comparison
    # Other comparison ops (!=, <, >, <=, >=) would go here, typically same precedence as ==
    '+': {'precedence': 2, 'associativity': 'left'},
    '-': {'precedence': 2, 'associativity': 'left'},
    '*': {'precedence': 3, 'associativity': 'left'},
    '/': {'precedence': 3, 'associativity': 'left'},
    '^': {'precedence': 5, 'associativity': 'right'},
    '**': {'precedence': 5, 'associativity': 'right'}
}
