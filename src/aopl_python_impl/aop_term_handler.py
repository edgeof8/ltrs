# aopl_python_impl/aop_term_handler.py

import cmath
import re
from typing import Dict
from .definitions import ValueTuple, LETTER_TO_EXPONENT_MAP, IMAGINARY_UNIT_J

COEFF_WORD_PARSER = re.compile(r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)([a-yA-Y]+)")

def calculate_word_exponent(word: str) -> int:
    total_exponent = 0
    for char in word.lower():
        # .get() will safely return 0 for 'z' or any other non-AoP char.
        total_exponent += LETTER_TO_EXPONENT_MAP.get(char, 0)
    return total_exponent

def get_term_value(term_str: str, variables: Dict[str, ValueTuple], kind: str) -> ValueTuple:
    if kind == 'NUMBER':
        return (complex(term_str), 0)
    if kind == 'CONSTANT_LITERAL':
        if term_str == '#j': return IMAGINARY_UNIT_J
        raise ValueError(f"Unknown constant: {term_str}")

    if kind == 'COEFF_WORD':
        match = COEFF_WORD_PARSER.match(term_str)
        if not match: raise ValueError(f"Invalid coefficient-word: {term_str}")
        coeff_str, word_str = match.groups()
        coeff = complex(float(coeff_str))
        expon = calculate_word_exponent(word_str)
        return (coeff, expon)

    if kind == 'IDENTIFIER':
        if term_str in variables:
            return variables[term_str]

        # If it's not a variable, check if it's a valid AoP word (now a-y).
        if all(c.lower() in LETTER_TO_EXPONENT_MAP for c in term_str):
            expon = calculate_word_exponent(term_str)
            return (1.0, expon)

        # If it contains 'z' or other non-AoP letters, it's an undefined variable.
        raise ValueError(f"Undefined variable or invalid word: '{term_str}'")

    raise ValueError(f"Unknown term kind: {kind}")
