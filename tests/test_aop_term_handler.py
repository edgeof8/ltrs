import pytest
from decimal import Decimal
from aopl_python_impl.definitions import LETTER_TO_EXPONENT_MAP
from aopl_python_impl.aop_value import AoPValue
from aopl_python_impl.aop_term_handler import (
    get_term_value,
    calculate_word_exponent,
    IMAGINARY_UNIT_J
)

def test_calculate_word_exponent():
    assert calculate_word_exponent('a') == 1
    assert calculate_word_exponent('b') == 2
    assert calculate_word_exponent('y') == 25
    assert calculate_word_exponent('A') == 26
    assert calculate_word_exponent('Y') == 50
    assert calculate_word_exponent('abc') == 6  # 1+2+3
    assert calculate_word_exponent('aA') == 27  # 1+26

def test_get_term_value_number():
    assert get_term_value("5", {}, 'NUMBER') == AoPValue(5+0j, 0.0)
    assert get_term_value("3.14", {}, 'NUMBER') == AoPValue(3.14+0j, 0.0)
    assert get_term_value("-2.5e3", {}, 'NUMBER') == AoPValue(-2500+0j, 0.0)

def test_get_term_value_constant_j():
    assert get_term_value("#j", {}, 'CONSTANT_LITERAL') == IMAGINARY_UNIT_J

def test_get_term_value_coeff_word():
    result = get_term_value("3.14abc", {}, 'COEFF_WORD')
    assert result.coeff == 3.14+0j
    assert result.exponent == 6.0  # a+b+c = 1+2+3

def test_get_term_value_identifier():
    variables = {'x': AoPValue(2+0j, 3.0)}
    assert get_term_value("x", variables, 'IDENTIFIER') == variables['x']
    assert get_term_value("abc", {}, 'IDENTIFIER') == AoPValue(1.0, 6.0)

def test_get_term_value_errors():
    with pytest.raises(ValueError, match="Unknown constant"):
        get_term_value("#x", {}, 'CONSTANT_LITERAL')

    with pytest.raises(ValueError, match="Invalid coeff-word"):
        get_term_value("3.14", {}, 'COEFF_WORD')

    with pytest.raises(ValueError, match="Undefined variable"):
        get_term_value("x", {}, 'IDENTIFIER')

    with pytest.raises(ValueError, match="Unknown term kind"):
        get_term_value("", {}, 'UNKNOWN_KIND')
