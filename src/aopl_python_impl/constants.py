# aopl_python_impl/constants.py
#
# This module serves as a single source of truth for the constants that define
# the grammar and notation of the Alphabet of Powers (AoP) language.

import re, string

# --- Letter to Exponent Mapping ---
# Defines the core AoP notation where letters correspond to integer exponents.
LOWERCASE_AOP_LETTERS = string.ascii_lowercase[:25]
UPPERCASE_AOP_LETTERS = string.ascii_uppercase[:25]

# The primary map used for parsing literals.
LETTER_TO_EXPONENT_MAP = {c: i+1 for i, c in enumerate(LOWERCASE_AOP_LETTERS)}
LETTER_TO_EXPONENT_MAP.update({c: i+26 for i, c in enumerate(UPPERCASE_AOP_LETTERS)})
LETTER_TO_EXPONENT_MAP['Z'] = 100
LETTER_TO_EXPONENT_MAP['z'] = 100 # 'z' is an alias for 'Z' for convenience.

# The reverse map used for formatting AoPValues back into symbolic strings.
# We exclude 'z' to ensure 'Z' is the canonical representation for 100.
EXPONENT_TO_LETTER_MAP = {v: k for k, v in LETTER_TO_EXPONENT_MAP.items() if k != 'z'}

# --- Tokenizer Regex ---
TOKEN_REGEX = re.compile(r"(\*\*|==?|[+\-*/^()])")

# --- Operator Definitions ---
# Defines the supported operators, their precedence, and their associativity.
# This dictionary is the core of the parser's logic for handling order of operations.
# Higher precedence values are evaluated first.
OPERATORS = {
    '=': {'precedence': 1, 'associativity': 'right'},  # Assignment
    '==': {'precedence': 1.5, 'associativity': 'left'}, # Equality comparison
    '+': {'precedence': 2, 'associativity': 'left'},   # Addition
    '-': {'precedence': 2, 'associativity': 'left'},   # Subtraction
    '*': {'precedence': 3, 'associativity': 'left'},   # Multiplication
    '/': {'precedence': 3, 'associativity': 'left'},   # Division (integer)
    '^': {'precedence': 5, 'associativity': 'right'},  # Power (right-associative)
    '**': {'precedence': 5, 'associativity': 'right'}  # Power (alias)
}
