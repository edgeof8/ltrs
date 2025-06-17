# aopl_python_impl/aop_operations.py

import math
import cmath
from .aop_value import AoPValue, PracticalLimitError
from decimal import Decimal
from typing import Union, Optional

DEBUG_AOP_OPERATIONS = False # Global debug flag for this module

def add_values(v1: AoPValue, v2: AoPValue, base: int) -> AoPValue:
    try: return AoPValue(v1.to_numerical(base) + v2.to_numerical(base))
    except OverflowError: raise OverflowError("Cannot add/subtract values of this magnitude.")

def subtract_values(v1: AoPValue, v2: AoPValue, base: int) -> AoPValue:
    try: return AoPValue(v1.to_numerical(base) - v2.to_numerical(base))
    except OverflowError: raise OverflowError("Cannot add/subtract values of this magnitude.")

def multiply_values(v1: AoPValue, v2: AoPValue) -> AoPValue:
    v1_is_num = v1.is_numeric()
    v2_is_num = v2.is_numeric()

    if v1_is_num and not v2_is_num:
        return AoPValue(v1.coeff * v2.coeff, v2.exponent)

    if not v1_is_num and v2_is_num:
        return AoPValue(v1.coeff * v2.coeff, v1.exponent)

    if not v1_is_num and not v2_is_num:
        raise NotImplementedError("Multiplication of two recursive AoP values is not yet supported.")

    exp1_val = v1.exponent
    assert isinstance(exp1_val, (complex, Decimal))
    exp2_val = v2.exponent
    assert isinstance(exp2_val, (complex, Decimal))

    if isinstance(exp1_val, complex) or isinstance(exp2_val, complex):
        exponent_result = complex(exp1_val) + complex(exp2_val)
    else:
        exponent_result = exp1_val + exp2_val

    return AoPValue(v1.coeff * v2.coeff, exponent_result)


def divide_values(v1: AoPValue, v2: AoPValue) -> AoPValue:
    if cmath.isclose(v2.coeff, 0j): raise ZeroDivisionError("Division by zero.")
    if not v1.is_numeric() and v2.is_numeric() and v2.exponent == 0:
        return AoPValue(v1.coeff / v2.coeff, v1.exponent)

    if not v1.is_numeric() or not v2.is_numeric():
        raise NotImplementedError("Division with recursive exponents is not supported")

    exp1_val = v1.exponent
    assert isinstance(exp1_val, (complex, Decimal))
    exp2_val = v2.exponent
    assert isinstance(exp2_val, (complex, Decimal))

    if isinstance(exp1_val, complex) or isinstance(exp2_val, complex):
        exponent_result = complex(exp1_val) - complex(exp2_val)
    else:
        exponent_result = exp1_val - exp2_val

    return AoPValue(v1.coeff / v2.coeff, exponent_result)

def multiply_complex_by_aop(scalar: Union[complex, Decimal], val_aop: AoPValue) -> AoPValue:
    if DEBUG_AOP_OPERATIONS: print(f"[DEBUG multiply_complex_by_aop] scalar: {scalar}, val_aop: {val_aop}")
    scalar_aop = AoPValue(coeff=complex(scalar), exponent=0)
    return multiply_values(scalar_aop, val_aop)


def power_value(base_val: AoPValue, power_val: AoPValue, base: int) -> AoPValue:
    if DEBUG_AOP_OPERATIONS: print(f"[DEBUG power_value] base_val: {base_val}, power_val: {power_val}, base: {base}")

    base_val = simplify_value(base_val, base)
    power_val = simplify_value(power_val, base)
    if DEBUG_AOP_OPERATIONS: print(f"[DEBUG power_value AFTER_SIMPLIFY_ARGS] base_val: {base_val}, power_val: {power_val}")

    try:
        power_numerical = power_val.to_numerical(base)
        if DEBUG_AOP_OPERATIONS: print(f"[DEBUG power_value] Power is numerically representable as {power_numerical}")

        if not base_val.is_numeric():
            if not cmath.isclose(base_val.coeff, 1.0):
                raise NotImplementedError("Recursive base with coeff!=1 not supported")
            assert isinstance(base_val.exponent, AoPValue)
            new_exponent = multiply_complex_by_aop(power_numerical, base_val.exponent)
            return AoPValue(1.0, new_exponent)

        log_coeff = 0.0 + 0.0j
        if not cmath.isclose(base_val.coeff, 1.0):
            if base_val.coeff == 0: return AoPValue(0.0, 0.0)
            log_coeff = cmath.log(base_val.coeff) / cmath.log(base)

        base_exponent_numeric = complex(base_val.exponent)
        final_exponent = power_numerical * (log_coeff + base_exponent_numeric)
        return AoPValue(1.0, final_exponent)

    except (OverflowError, PracticalLimitError):
        if DEBUG_AOP_OPERATIONS: print(f"[DEBUG power_value] Power {power_val} is too large. Switching to symbolic hyper-power.")

        if not base_val.is_numeric():
             raise NotImplementedError("Recursive base to recursive (hyper) power is not yet supported.")

        log_coeff = 0.0 + 0.0j
        if not cmath.isclose(base_val.coeff, 1.0):
            if base_val.coeff == 0: return AoPValue(0.0, 0.0)
            log_coeff = cmath.log(base_val.coeff) / cmath.log(base)

        total_base_exponent = log_coeff + complex(base_val.exponent)
        new_exponent = multiply_complex_by_aop(total_base_exponent, power_val)
        return AoPValue(1.0, new_exponent)


def simplify_value(val: AoPValue, base: int) -> AoPValue:
    if isinstance(val.exponent, AoPValue):
        simplified_inner_exponent = simplify_value(val.exponent, base)
        if val.exponent is not simplified_inner_exponent:
            if DEBUG_AOP_OPERATIONS:
                print(f"[DEBUG simplify_value] RecursiveUpdate: Original exponent {val.exponent} was simplified to {simplified_inner_exponent}")
            val = AoPValue(val.coeff, simplified_inner_exponent)

    if val.is_numeric():
        coeff = val.coeff
        current_exponent_val = val.exponent
        if base <= 1 or cmath.isclose(coeff, 0j) or not cmath.isclose(coeff.imag, 0) or coeff.real <= 0:
            return val

        exp_real_part_dec: Optional[Decimal] = None
        if isinstance(current_exponent_val, Decimal):
            exp_real_part_dec = current_exponent_val
        elif isinstance(current_exponent_val, complex):
            if cmath.isclose(current_exponent_val.imag, 0):
                try: exp_real_part_dec = Decimal(str(current_exponent_val.real))
                except: return val
            else: return val
        else: return val

        if exp_real_part_dec is None: return val

        try:
            p_float = math.log(coeff.real, float(base))
            if math.isclose(p_float, round(p_float)):
                p_decimal = Decimal(int(round(p_float)))
                new_exponent_decimal = exp_real_part_dec + p_decimal
                if DEBUG_AOP_OPERATIONS: print(f"[DEBUG simplify_value] NumericSimplify (log): {val} -> AoPValue(1.0, {new_exponent_decimal}) with p={p_decimal}")
                return AoPValue(1.0, new_exponent_decimal)
        except (ValueError, OverflowError, TypeError):
            pass

    return val
