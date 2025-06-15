# aopl_python_impl/aop_operations.py

import math
import cmath
from .definitions import ValueTuple

def add_values(val1: ValueTuple, val2: ValueTuple, base: int) -> ValueTuple:
    try:
        num1 = val1[0] * (base ** val1[1])
        num2 = val2[0] * (base ** val2[1])
        return (num1 + num2, 0)
    except OverflowError:
        raise OverflowError("Cannot add/subtract numbers of this magnitude.")

def subtract_values(val1: ValueTuple, val2: ValueTuple, base: int) -> ValueTuple:
    try:
        num1 = val1[0] * (base ** val1[1])
        num2 = val2[0] * (base ** val2[1])
        return (num1 - num2, 0)
    except OverflowError:
        raise OverflowError("Cannot add/subtract numbers of this magnitude.")

def multiply_values(val1: ValueTuple, val2: ValueTuple) -> ValueTuple:
    return (val1[0] * val2[0], val1[1] + val2[1])

def divide_values(val1: ValueTuple, val2: ValueTuple) -> ValueTuple:
    if cmath.isclose(val2[0], 0j): raise ZeroDivisionError("Division by zero.")
    return (val1[0] / val2[0], val1[1] - val2[1])

def power_value(val: ValueTuple, n_power: float, base: int) -> ValueTuple:
    coeff, expon = val
    if cmath.isclose(coeff, 0j):
        if math.isclose(n_power, 0.0): return (1.0, 0)
        if n_power > 0: return (0j, 0)
        raise ZeroDivisionError("0 cannot be raised to a negative power.")

    if cmath.isclose(coeff, 1.0) and math.isclose(n_power, round(n_power)):
        try:
            new_expon = expon * int(round(n_power))
            return (1.0, new_expon)
        except OverflowError:
            raise OverflowError("Resulting exponent from symbolic power is too large.")

    try:
        full_value = coeff * (base ** expon)
        return (full_value ** n_power, 0)
    except OverflowError:
        raise OverflowError(f"Base '{val}' is too large to raise to power '{n_power}'.")

def simplify_value(val: ValueTuple, base: int) -> ValueTuple:
    coeff, expon = val
    if base == 1: return (coeff, 0)
    if base < 1 or cmath.isclose(coeff, 0j) or not cmath.isclose(coeff.imag, 0) or coeff.real <= 0:
        return val
    try:
        p = math.log(coeff.real, base)
        if math.isclose(p, round(p)):
            i = int(round(p))
            new_c = coeff / (base ** i)
            if cmath.isclose(new_c, 1.0): return (1.0, expon + i)
    except (ValueError, OverflowError): pass
    return val
