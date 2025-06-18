# aopl_python_impl/aop_operations.py
import cmath, decimal
from decimal import Decimal
from typing import List, Union
from .aop_value import AoPValue, AoPTerm
from .definitions import PracticalLimitError, AoPError

def simplify_value(value: AoPValue, base: int) -> AoPValue:
    """A safe, non-recursive function to combine like terms and absorb coefficients."""
    if len(value.terms) <= 1:
        # Even for a single term, try to absorb its coefficient if possible.
        if len(value.terms) == 1:
            term = value.terms[0]
            if not cmath.isclose(term.coeff, 1.0) and not isinstance(term.exponent, AoPValue):
                try:
                    log_coeff = cmath.log(term.coeff) / cmath.log(base)
                    if cmath.isfinite(log_coeff) and cmath.isclose(log_coeff.imag, 0):
                        new_exp_val = log_coeff.real + complex(term.exponent)
                        return AoPValue([AoPTerm(1.0, new_exp_val)])
                except (ValueError, ZeroDivisionError):
                    pass # Cannot absorb, return original term.
        return value

    # Combine like terms
    exp_map = {}
    for term in value.terms:
        key = repr(term.exponent)
        if key in exp_map:
            exp_map[key].coeff += term.coeff
        else:
            exp_map[key] = AoPTerm(term.coeff, term.exponent)

    new_terms = [t for t in exp_map.values() if not cmath.isclose(t.coeff, 0)]

    if not new_terms: return AoPValue.from_number(0)
    return AoPValue(new_terms)

def add_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    """Adds two AoPValues by combining their terms and simplifying."""
    return simplify_value(AoPValue(op1.terms + op2.terms), base)

def subtract_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    """Subtracts op2 from op1 by negating op2's terms and adding."""
    neg_op2_terms = [AoPTerm(-t.coeff, t.exponent) for t in op2.terms]
    return add_values(op1, AoPValue(neg_op2_terms), base)

def multiply_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    """Symbolically multiplies two AoPValues using the distributive law."""
    if not op1.terms or not op2.terms: return AoPValue()

    new_terms: List[AoPTerm] = []
    for t1 in op1.terms:
        for t2 in op2.terms:
            new_coeff = t1.coeff * t2.coeff

            e1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_number(t1.exponent)
            e2_aop = t2.exponent if isinstance(t2.exponent, AoPValue) else AoPValue.from_number(t2.exponent)
            new_exp_aop = add_values(e1_aop, e2_aop, base)

            # If the resulting exponent is just a number, unwrap it to a primitive.
            final_exp = new_exp_aop
            if len(new_exp_aop.terms) == 1 and new_exp_aop.terms[0].is_numeric_exponent_zero():
                final_exp = new_exp_aop.terms[0].coeff

            new_terms.append(AoPTerm(new_coeff, final_exp))

    return simplify_value(AoPValue(new_terms), base)

def power_value(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    # Symbolic evaluation is only well-defined for a single-term base.
    if len(op1.terms) == 1:
        t1 = op1.terms[0]
        try:
            # Use the identity: (C*a^E1)^op2 = a^(op2 * (log_base(C) + E1))
            log_coeff_aop = AoPValue.from_number(cmath.log(t1.coeff) / cmath.log(base))
            e1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_number(t1.exponent)

            # This is the term inside the parentheses: (log_base(C) + E1)
            inner_exp = add_values(log_coeff_aop, e1_aop, base)

            # Now multiply by the outer exponent, op2
            final_exp = multiply_values(op2, inner_exp, base)

            # The result is base^(final_exp), which is represented as 1 * a^(final_exp)
            # The exponent itself might be a simple number, so we unwrap it.
            if len(final_exp.terms) == 1 and final_exp.terms[0].is_numeric_exponent_zero():
                return AoPValue([AoPTerm(1.0, final_exp.terms[0].coeff)])
            else:
                return AoPValue([AoPTerm(1.0, final_exp)])

        except (ValueError, ZeroDivisionError, PracticalLimitError):
            pass # Fall through to numerical if symbolic fails.

    # Numerical fallback for sums or if the symbolic path fails.
    try:
        num1 = op1.to_numerical(base)
        num2 = op2.to_numerical(base)
        if cmath.isclose(num1, 0) and num2.real < 0: raise ZeroDivisionError("0 to a negative power.")
        result_num = num1 ** num2
        if not cmath.isfinite(result_num): raise PracticalLimitError("Power result is not a finite number.")
        return AoPValue.from_number(result_num)
    except (PracticalLimitError, OverflowError, ZeroDivisionError, NotImplementedError) as e:
        raise AoPError(f"Cannot evaluate power for expression: {op1!r}^{op2!r} ({e})")

def divide_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    """Divides op1 by op2, equivalent to op1 * (op2^-1)."""
    try:
        inverse_op2 = power_value(op2, AoPValue.from_number(-1), base)
        return multiply_values(op1, inverse_op2, base)
    except AoPError:
        try:
            num1 = op1.to_numerical(base)
            num2 = op2.to_numerical(base)
            if cmath.isclose(num2, 0): raise ZeroDivisionError("Division by zero.")
            return AoPValue.from_number(num1 / num2)
        except (OverflowError, PracticalLimitError, NotImplementedError, ZeroDivisionError) as e:
            raise AoPError(f"Cannot perform division: {e}")

def final_simplify(value: AoPValue, base: int) -> AoPValue:
    """The master simplification function called once at the end of evaluation."""
    simplified = simplify_value(value, base)
    return simplified
