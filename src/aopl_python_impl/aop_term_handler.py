# FILE: src/aopl_python_impl/aop_term_handler.py

import re
from .definitions import LETTER_TO_EXPONENT_MAP
from .aop_value import AoPValue # This import is fine and necessary

# FIX: Define the constant here instead of importing it.
IMAGINARY_UNIT_J: AoPValue = AoPValue(complex(0, 1), 0.0)

COEFF_WORD_PARSER = re.compile(r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)([a-yA-Y]+)")

def calculate_word_exponent(word: str) -> int:
    return sum(LETTER_TO_EXPONENT_MAP.get(char, 0) for char in word.lower())

def get_term_value(term_str: str, variables: dict[str, AoPValue], kind: str) -> AoPValue:
    if kind == 'NUMBER':
        return AoPValue(complex(term_str), 0.0)

    if kind == 'CONSTANT_LITERAL':
        if term_str == '#j':
            # Use the locally defined constant
            return IMAGINARY_UNIT_J
        raise ValueError(f"Unknown constant: {term_str}")

    if kind == 'COEFF_WORD':
        match = COEFF_WORD_PARSER.match(term_str)
        if not match:
            raise ValueError(f"Invalid coeff-word: {term_str}")
        coeff = complex(float(match.group(1)))
        expon = float(calculate_word_exponent(match.group(2)))
        return AoPValue(coeff, expon)

    if kind == 'IDENTIFIER':
        if term_str in variables:
            return variables[term_str]
        if all(c.lower() in LETTER_TO_EXPONENT_MAP for c in term_str):
            expon = float(calculate_word_exponent(term_str))
            return AoPValue(1.0, expon)
        raise ValueError(f"Undefined variable or invalid word: '{term_str}'")

    raise ValueError(f"Unknown term kind: {kind}")
