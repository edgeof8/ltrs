# aopl_python_impl/aop_term_handler.py

import re
from .definitions import ValueTuple, IMAGINARY_UNIT_J, LETTER_TO_EXPONENT_MAP

COEFF_WORD_PARSER = re.compile(r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)([a-yA-Y]+)")

def calculate_word_exponent(word: str) -> int:
    """Calculates the total exponent for a word based on the a-y alphabet."""
    total_exponent = 0
    for char in word.lower():
        total_exponent += LETTER_TO_EXPONENT_MAP.get(char, 0)
    return total_exponent

def get_term_value(term_str: str, variables: dict[str, ValueTuple], kind: str) -> ValueTuple:
    if kind == 'NUMBER':
        return (complex(term_str), 0)
    if kind == 'CONSTANT_LITERAL':
        if term_str == '#j': return IMAGINARY_UNIT_J
        raise ValueError(f"Unknown constant: {term_str}")

    if kind == 'COEFF_WORD':
        match = COEFF_WORD_PARSER.match(term_str)
        if not match: raise ValueError(f"Invalid coefficient-word: {term_str}")
        coeff = complex(float(match.group(1)))
        expon = calculate_word_exponent(match.group(2))
        return (coeff, expon)

    if kind == 'IDENTIFIER':
        # Check if it's a defined variable first.
        if term_str in variables:
            return variables[term_str]

        # If not a variable, check if it's a valid AoP word (now a-y).
        if all(c.lower() in LETTER_TO_EXPONENT_MAP for c in term_str):
            expon = calculate_word_exponent(term_str)
            return (1.0, expon)

        # If it contains 'z' or other non-AoP letters, it's an undefined variable.
        raise ValueError(f"Undefined variable or invalid word: '{term_str}'")

    raise ValueError(f"Unknown term kind: {kind}")
