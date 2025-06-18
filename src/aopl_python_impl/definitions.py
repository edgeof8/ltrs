# aopl_python_impl/definitions.py
import re, string
from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple
from enum import Enum

class OutputFormatMode(Enum): AUTO = "auto"; AOP = "aop"; SCIENTIFIC = "sci"; NUMERICAL = "num"
class Token(NamedTuple): kind: str; value: str; start: int; end: int
class AoPError(ValueError):
    def __init__(self, message: str, token: Optional[Token] = None):
        self.message, self.token = message, token
        super().__init__(message)

LOWERCASE_AOP_LETTERS = string.ascii_lowercase[:25]
UPPERCASE_AOP_LETTERS = string.ascii_uppercase[:25]
LETTER_TO_EXPONENT_MAP: Dict[str, int] = {**{l: i + 1 for i, l in enumerate(LOWERCASE_AOP_LETTERS)}, **{l: i + 26 for i, l in enumerate(UPPERCASE_AOP_LETTERS)}}
EXPONENT_TO_LETTER_MAP: Dict[int, str] = {v: k for k, v in LETTER_TO_EXPONENT_MAP.items()}

_opt_sign = r"[+-]?"
_number_bare = r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?"
_integer_bare = r"\d+"
_any_number = f"(?:{_number_bare}|{_integer_bare})"
_number_signed = f"{_opt_sign}{_any_number}"
_word_simple = r"[a-yA-Y]+"
_variable_name = r"[zZ_][a-zA-Z0-9_$]*"

TOKEN_SPECIFICATION: List[Tuple[str, str]] = [
    ('COEFF_WORD', f"{_number_signed}{_word_simple}"),
    ('NUMBER', _number_signed),
    ('IDENTIFIER', _word_simple),
    ('OPERATOR', r"\*\*|[\+\-\*\/\^=]"),
    ('LPAREN', r"\("), ('RPAREN', r"\)"),
    ('WHITESPACE', r"\s+"), ('MISMATCH', r"."),
]
TOKEN_REGEX: Pattern[str] = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))
OPERATORS: Dict[str, Dict] = {'=': {'precedence': 1, 'associativity': 'right'}, '+': {'precedence': 2, 'associativity': 'left'}, '-': {'precedence': 2, 'associativity': 'left'}, '*': {'precedence': 3, 'associativity': 'left'}, '/': {'precedence': 3, 'associativity': 'left'}, '^': {'precedence': 5, 'associativity': 'right'}, '**': {'precedence': 5, 'associativity': 'right'}}
