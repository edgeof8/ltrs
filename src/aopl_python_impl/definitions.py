# aopl_python_impl/definitions.py

import string
from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple
from enum import Enum
import re

class OutputFormatMode(Enum):
    AUTO = "auto"
    AOP = "aop"
    SCIENTIFIC = "sci"
    NUMERICAL = "num"

class PowerAssociativity(Enum):
    LEFT = "left"
    RIGHT = "right"

class Token(NamedTuple):
    kind: str
    value: str
    start: int
    end: int

class AoPError(ValueError):
    def __init__(self, message: str, token: Optional[Token] = None):
        self.message = message
        self.token = token
        super().__init__(message)

ValueTuple = tuple[complex, int | tuple[str, int, int]]
IMAGINARY_UNIT_J: ValueTuple = (complex(0, 1), 0)

AOP_LETTERS = string.ascii_lowercase[:25] # 'a' through 'y'
LETTER_TO_EXPONENT_MAP: Dict[str, int] = {letter: i + 1 for i, letter in enumerate(AOP_LETTERS)}
EXPONENT_TO_LETTER_MAP: Dict[int, str] = {i + 1: letter for i, letter in enumerate(AOP_LETTERS)}

_opt_sign = r"[+-]?"
_number_bare = r"(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
_number_signed = fr"{_opt_sign}{_number_bare}"
_word_simple = r"[a-yA-Y]+"
_identifier_raw = r"[a-zA-Z_$][a-zA-Z0-9_$]*"
_hashtag_constants = r"pi|e|j"

TOKEN_SPECIFICATION: List[Tuple[str, str]] = [
    ('FUNCTION', r"sqrt|log|ln|log2|sin|cos|tan"),
    ('CONSTANT_LITERAL', fr"#(?:{_hashtag_constants})"),
    ('OPERATOR', r"[\+\-\*\/\^]"),
    ('COEFF_WORD', fr"{_number_signed}{_word_simple}"),
    ('NUMBER', _number_signed),
    ('IDENTIFIER', _identifier_raw),
    ('LPAREN', r"\("),
    ('RPAREN', r"\)"),
    ('COMMA', r","),
    ('MISMATCH', r"."),
]

TOKEN_REGEX: Pattern[str] = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))

OPERATORS: Dict[str, Dict] = {
    '+': {'precedence': 2, 'associativity': 'left'},
    '-': {'precedence': 2, 'associativity': 'left'},
    '*': {'precedence': 3, 'associativity': 'left'},
    '/': {'precedence': 3, 'associativity': 'left'},
    '^': {'precedence': 5, 'associativity': 'right'}, # Default, parser adapts
    '_UMINUS': {'precedence': 4, 'associativity': 'right'},
    '_UPLUS': {'precedence': 4, 'associativity': 'right'},
}
