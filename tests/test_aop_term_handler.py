# tests/test_aop_term_handler.py
import pytest
from decimal import Decimal
from aopl_python_impl.aop_value import AoPValue, AoPTerm
from aopl_python_impl.aop_term_handler import get_term_value, IMAGINARY_UNIT_J
import cmath # Import cmath

def assert_single_term_value(value: AoPValue, coeff: complex, exponent: Decimal):
    assert len(value.terms) == 1
    term = value.terms[0]
    assert cmath.isclose(term.coeff, coeff)
    assert isinstance(term.exponent, Decimal) # Exponent should be Decimal for these simple cases
    assert term.exponent == exponent

def test_get_term_value_number():
    val = get_term_value("123.45", {}, 'NUMBER')
    assert_single_term_value(val, 123.45+0j, Decimal(0))

def test_get_term_value_imaginary_unit():
    # This test assumes CONSTANT_LITERAL is part of your TOKEN_SPECIFICATION
    # If not, you might need to adjust the test or the tokenizer
    pass # Skipping as #j is not in the final TOKEN_SPECIFICATION

def test_get_term_value_coeff_word():
    val = get_term_value("2.5c", {}, 'COEFF_WORD')
    assert_single_term_value(val, 2.5+0j, Decimal(3))

def test_get_term_value_identifier():
    val = get_term_value("cat", {}, 'IDENTIFIER')
    assert_single_term_value(val, 1.0+0j, Decimal(24)) # c=3, a=1, t=20 -> 3+1+20=24

def test_get_term_value_variable():
    # This test assumes 'VARIABLE' is a token kind handled by get_term_value
    var_val = AoPValue.from_number(Decimal('500')) # Create an AoPValue for the variable
    variables = {"z1": var_val}
    val = get_term_value("z1", variables, 'VARIABLE')
    assert val is var_val # Should return the exact AoPValue object

def test_undefined_variable_identifier_fallback():
    # If "undefined" is not in variables, it should be treated as an IDENTIFIER (AoP word)
    val = get_term_value("undefined", {}, 'IDENTIFIER')
    # u=21, n=14, d=4, e=5, f=6, i=9 -> 21+14+4+5+6+9+14+5+4 = 78
    assert_single_term_value(val, 1.0+0j, Decimal(78))

def test_undefined_variable_error_if_variable_kind():
    # If explicitly asking for a VARIABLE that's not defined, it should error
    with pytest.raises(ValueError, match="Undefined variable: undefined_var"):
         get_term_value("undefined_var", {}, 'VARIABLE')

def test_invalid_coeff_word_error():
    with pytest.raises(ValueError, match="Invalid coeff-word: 123.45"): # Number only is not coeff-word
        get_term_value("123.45", {}, 'COEFF_WORD')
    with pytest.raises(ValueError, match="Invalid coeff-word: word"): # Word only is not coeff-word
        get_term_value("word", {}, 'COEFF_WORD')


def test_unknown_term_kind_error():
    with pytest.raises(ValueError, match="Unknown term kind: BOGUS_KIND"):
        get_term_value("anything", {}, 'BOGUS_KIND')
