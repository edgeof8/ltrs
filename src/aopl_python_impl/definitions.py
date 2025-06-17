# FILE: src/aopl_python_impl/definitions.py

import string
import re
from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple
from enum import Enum
# DO NOT IMPORT AoPValue or any other local project modules here.
# This file must be self-contained.

class OutputFormatMode(Enum):
    AUTO = "auto"
    AOP = "aop"
    SCIENTIFIC = "sci"
    NUMERICAL = "num"

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

# The IMAGINARY_UNIT_J constant has been permanently moved to aop_term_handler.py

# ... (rest of the file is correct and remains unchanged) ...

LOWERCASE_AOP_LETTERS = string.ascii_lowercase[:25] # a-y
UPPERCASE_AOP_LETTERS = string.ascii_uppercase[:25] # A-Y

LETTER_TO_EXPONENT_MAP: Dict[str, int] = {
    **{letter: i + 1 for i, letter in enumerate(LOWERCASE_AOP_LETTERS)},
    **{letter: i + 26 for i, letter in enumerate(UPPERCASE_AOP_LETTERS)}
}
EXPONENT_TO_LETTER_MAP: Dict[int, str] = {v: k for k, v in LETTER_TO_EXPONENT_MAP.items()}

# ... (rest of regex and OPERATORS definitions) ...
_opt_sign = r"[+-]?"
_number_bare = r"(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
_number_signed = fr"{_opt_sign}{_number_bare}"
_word_simple = r"[a-yA-Y]+"
_variable_name = r"[zZ_][a-zA-Z0-9_$]*"

TOKEN_SPECIFICATION: List[Tuple[str, str]] = [
    ('FUNCTION', r"sqrt|log|ln|log2|sin|cos|tan"),
    ('CONSTANT_LITERAL', fr"#(?:pi|e|j)"),
    ('OPERATOR', r"\*\*|[\+\-\*\/\^=]"),
    ('COEFF_WORD', fr"{_number_signed}{_word_simple}"),
    ('NUMBER', _number_signed),
    ('IDENTIFIER', _word_simple),
    ('VARIABLE', _variable_name),
    ('LPAREN', r"\("),
    ('RPAREN', r"\)"),
    ('COMMA', r","),
    ('WHITESPACE', r"\s+"),
    ('MISMATCH', r"."),
]

TOKEN_REGEX: Pattern[str] = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))

OPERATORS: Dict[str, Dict] = {
    '=': {'precedence': 1, 'associativity': 'right'},
    '+': {'precedence': 2, 'associativity': 'left'},
    '-': {'precedence': 2, 'associativity': 'left'},
    '*': {'precedence': 3, 'associativity': 'left'},
    '/': {'precedence': 3, 'associativity': 'left'},
    '^': {'precedence': 5, 'associativity': 'right'},
    '**': {'precedence': 6, 'associativity': 'right'},
}
