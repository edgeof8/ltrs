# aopl_python_impl/aop_operations.py
import cmath, decimal
from decimal import Decimal
from typing import List, Union
from .aop_value import AoPValue, AoPTerm
from .definitions import PracticalLimitError, AoPError
# aopl_python_impl/aop_operations.py

def simplify_value(value: AoPValue, base: int) -> AoPValue:
    if len(value.terms) <= 1:
        return value

    # Use a dictionary to group terms by their exponent.
    # The key can be a number (for numeric exponents) or a string (for symbolic ones).
    exp_map = {}

    for term in value.terms:
        key = None
        if isinstance(term.exponent, AoPValue):
            # For symbolic exponents, we need a stable, hashable representation.
            # Recursively simplifying first makes it more stable.
            simplified_exp = simplify_value(term.exponent, base)
            key = repr(simplified_exp)
            exponent_val = simplified_exp
        else:
            key = complex(term.exponent)
            exponent_val = term.exponent

        if key in exp_map:
            exp_map[key].coeff += term.coeff
        else:
            exp_map[key] = AoPTerm(term.coeff, exponent_val)

    # Rebuild the list of terms, filtering out any that cancelled to zero.
    new_terms = [t for t in exp_map.values() if not cmath.isclose(t.coeff, 0)]

    # If all terms cancelled, return a canonical zero.
    if not new_terms:
        return AoPValue.from_number(0)

    return AoPValue(new_terms)
def add_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    return simplify_value(AoPValue(op1.terms + op2.terms), base)

def subtract_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    neg_op2_terms = [AoPTerm(-t.coeff, t.exponent) for t in op2.terms]
    return simplify_value(AoPValue(op1.terms + neg_op2_terms), base)

def multiply_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    # FIX: Default to symbolic multiplication (distributive law).
    # This is essential for correctness. (t1*t2*...)*(tA*tB*...)
    if not op1.terms or not op2.terms:
        return AoPValue()

    new_terms: List[AoPTerm] = []
    for t1 in op1.terms:
        for t2 in op2.terms:
            # New coefficient is the product of the old ones.
            new_coeff = t1.coeff * t2.coeff

            # New exponent is the sum of the old ones.
            # Convert exponents to AoPValue to use add_values.
            exp1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_number(t1.exponent)
            exp2_aop = t2.exponent if isinstance(t2.exponent, AoPValue) else AoPValue.from_number(t2.exponent)

            # add_values will correctly handle number+number, number+symbolic, etc.
            new_exp = add_values(exp1_aop, exp2_aop, base)

            new_terms.append(AoPTerm(new_coeff, new_exp))

    # Simplify the resulting sum of new terms.
    return simplify_value(AoPValue(new_terms), base)

def divide_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    try:
        num1 = op1.to_numerical(base)
        num2 = op2.to_numerical(base)
        if cmath.isclose(num2, 0): raise ZeroDivisionError("Division by zero.")
        return AoPValue.from_number(num1 / num2)
    except (OverflowError, PracticalLimitError, NotImplementedError, ZeroDivisionError) as e:
        raise AoPError(f"Cannot perform division: {e}")

# aopl_python_impl/aop_operations.py

def power_value(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    # Symbolic path: (C*a^E1)^E2 = a^(E2 * (log(C) + E1))
    # This is the primary path for single-term bases, crucial for hyper-powers.
    if len(op1.terms) == 1:
        t1 = op1.terms[0]
        try:
            # Calculate log_base(C)
            log_base_C1_aop = AoPValue()
            if not cmath.isclose(t1.coeff, 0):
                log_coeff_val = cmath.log(t1.coeff) / cmath.log(base)
                if not cmath.isfinite(log_coeff_val):
                    raise PracticalLimitError("Log of coefficient is not finite.")
                log_base_C1_aop = AoPValue.from_number(log_coeff_val)

            # Get E1 as an AoPValue
            E1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_number(t1.exponent)

            # Form the inner term: log(C) + E1
            log_base_op1 = add_values(log_base_C1_aop, E1_aop, base)

            # Multiply by the outer exponent: E2 * (log(C) + E1)
            new_exponent = multiply_values(op2, log_base_op1, base)

            # The result is base^(new_exponent), which is 1 * a^(new_exponent)
            return AoPValue([AoPTerm(1.0, new_exponent)])
        except (ValueError, PracticalLimitError, NotImplementedError):
            # If symbolic path fails, fall through to numerical attempt
            pass

    # Numerical fallback for sums of terms or if the symbolic path failed.
    try:
        num1 = op1.to_numerical(base)
        num2 = op2.to_numerical(base)
        if cmath.isclose(num1, 0) and num2.real < 0: raise ZeroDivisionError("0 to a negative power.")
        result_num = num1 ** num2
        if not cmath.isfinite(result_num): raise PracticalLimitError("Power result is not a finite number.")
        return AoPValue.from_number(result_num)
    except (PracticalLimitError, OverflowError, ZeroDivisionError, NotImplementedError) as e:
        raise AoPError(f"Cannot evaluate power for expression: {op1!r}^{op2!r} ({e})")
