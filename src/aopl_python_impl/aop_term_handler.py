# aopl_python_impl/aop_term_handler.py
import re
import math
from decimal import Decimal
from .aop_value import AoPValue, AoPTerm
from .definitions import LETTER_TO_EXPONENT_MAP

COEFF_WORD_PARSER = re.compile(r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)([a-yA-Y]+)")

def calculate_word_exponent(word: str) -> int:
    return sum(LETTER_TO_EXPONENT_MAP.get(char, 0) for char in word)

def get_term_value(term_str: str, variables: dict[str, AoPValue], kind: str) -> AoPValue:
    # This is the unified entry point. Everything becomes an AoPValue immediately.
    if kind == 'NUMBER':
        # A number like "110" becomes a term with exponent 0.
        return AoPValue.from_number(Decimal(term_str))
    if kind == 'COEFF_WORD':
        match = COEFF_WORD_PARSER.match(term_str)
        if not match: raise ValueError(f"Invalid coeff-word: {term_str}")
        coeff = complex(Decimal(match.group(1)))
        exponent = Decimal(calculate_word_exponent(match.group(2)))
        return AoPValue.from_term(AoPTerm(coeff, exponent))
    if kind == 'IDENTIFIER':
        if term_str in variables: return variables[term_str]
        # An identifier like "a" becomes a term with coeff 1 and its letter-value as the exponent.
        exponent = Decimal(calculate_word_exponent(term_str))
        return AoPValue.from_term(AoPTerm(complex(1.0), exponent))
    if kind == 'CONSTANT_LITERAL':
        # Constants are numbers, so they should be represented as a coefficient with an exponent of 0.
        if term_str == "#pi":
            return AoPValue.from_number(Decimal(math.pi))
        elif term_str == "#e":
            return AoPValue.from_number(Decimal(math.e))
        elif term_str == "#phi": # Golden ratio
            return AoPValue.from_number(Decimal("1.61803398874989484820"))
        elif term_str == "#tau": # 2*pi
            return AoPValue.from_number(Decimal(2 * math.pi))
        elif term_str == "#sqrt2":
            return AoPValue.from_number(Decimal(math.sqrt(2)))
        elif term_str == "#j": # Imaginary unit
            return AoPValue.from_number(complex(0, 1))
        else:
            raise ValueError(f"Unknown constant literal: {term_str}")

    raise ValueError(f"Unknown term kind: {kind}")
