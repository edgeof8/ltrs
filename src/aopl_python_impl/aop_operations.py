# aopl_python_impl/aop_operations.py

import math
import cmath
from .definitions import ValueTuple

# New SymbolicExponent structure
# Using a simple tuple for now: ("SFP", factor, power_base_exponent)
# "SFP" stands for Symbolic Factor Power, representing factor * (actual_base ^ power_base_exponent)
SymbolicExponent = tuple

def is_symbolic_exponent(exp_repr):
    return isinstance(exp_repr, tuple) and len(exp_repr) == 3 and exp_repr[0] == "SFP"

class EngineLogicError(Exception): # For internal logic errors
    pass

def add_values(val1: ValueTuple, val2: ValueTuple, base: int) -> ValueTuple:
    # Addition requires numerical evaluation, cannot easily keep symbolic exponents combined.
    # This might need to raise an error if exponents are symbolic and cannot be resolved.
    c1, e1_repr = val1
    c2, e2_repr = val2
    if is_symbolic_exponent(e1_repr) or is_symbolic_exponent(e2_repr):
        raise NotImplementedError("Addition/subtraction with unevaluated symbolic exponents is not supported.")
    if not isinstance(e1_repr, int) or not isinstance(e2_repr, int):
        raise TypeError("Exponents must be integers for addition.")
    try:
        num1 = c1 * (base ** e1_repr)
        num2 = c2 * (base ** e2_repr)
        return (num1 + num2, 0)
    except OverflowError:
        raise OverflowError("Result of addition/subtraction is too large to represent.")

def subtract_values(val1: ValueTuple, val2: ValueTuple, base: int) -> ValueTuple:
    c1, e1_repr = val1
    c2, e2_repr = val2
    if is_symbolic_exponent(e1_repr) or is_symbolic_exponent(e2_repr):
        raise NotImplementedError("Addition/subtraction with unevaluated symbolic exponents is not supported.")
    if not isinstance(e1_repr, int) or not isinstance(e2_repr, int):
        raise TypeError("Exponents must be integers for subtraction.")
    try:
        num1 = c1 * (base ** e1_repr)
        num2 = c2 * (base ** e2_repr)
        return (num1 - num2, 0)
    except OverflowError:
        raise OverflowError("Result of addition/subtraction is too large to represent.")

def multiply_values(val1: ValueTuple, val2: ValueTuple) -> ValueTuple:
    c1, e1_repr = val1
    c2, e2_repr = val2

    # (C1 * base^E1) * (C2 * base^E2) = (C1*C2) * base^(E1+E2)
    # If E1 or E2 are symbolic, this becomes complex.
    # For now, assume multiplication only happens on resolved integer exponents.
    if is_symbolic_exponent(e1_repr) or is_symbolic_exponent(e2_repr):
        raise NotImplementedError("Multiplication with unevaluated symbolic exponents is not supported.")
    if not isinstance(e1_repr, int) or not isinstance(e2_repr, int):
        raise TypeError("Exponents must be integers for multiplication.")
    try:
        new_coeff = c1 * c2
        new_expon = e1_repr + e2_repr
        return (new_coeff, new_expon)
    except OverflowError:
        raise OverflowError("Coefficient product too large in multiplication.")

def divide_values(val1: ValueTuple, val2: ValueTuple) -> ValueTuple:
    c1, e1_repr = val1
    c2, e2_repr = val2
    if is_symbolic_exponent(e1_repr) or is_symbolic_exponent(e2_repr):
        raise NotImplementedError("Division with unevaluated symbolic exponents is not supported.")
    if not isinstance(e1_repr, int) or not isinstance(e2_repr, int):
        raise TypeError("Exponents must be integers for division.")
    if cmath.isclose(c2, 0j): raise ZeroDivisionError("Division by zero.")
    try:
        new_coeff = c1 / c2
        new_expon = e1_repr - e2_repr
        return (new_coeff, new_expon)
    except OverflowError:
        raise OverflowError("Coefficient division resulted in overflow.")

MAX_E_FOR_DIRECT_BASE_POWER_CALC = 2000 # If E > this, base^E is too slow.

def power_values(base_vt: ValueTuple, power_vt: ValueTuple, base: int) -> ValueTuple:
    base_coeff, base_expon_repr = base_vt
    power_coeff, power_expon_repr = power_vt

    if cmath.isclose(base_coeff, 0j):
        if cmath.isclose(power_coeff, 0j) and (not is_symbolic_exponent(power_expon_repr) and power_expon_repr == 0):
            return (1.0, 0)
        return (0j, 0)

    # Case 1: Base is (1.0 * base^E1_int)
    if cmath.isclose(base_coeff, 1.0) and isinstance(base_expon_repr, int):
        E1_int = base_expon_repr

        # Subcase 1.1: Power is (1.0 * base^E2_int)
        if cmath.isclose(power_coeff, 1.0) and isinstance(power_expon_repr, int):
            E2_int = power_expon_repr
            # We want to compute NewExp = E1_int * (base ** E2_int)
            if E2_int > MAX_E_FOR_DIRECT_BASE_POWER_CALC:
                # Return symbolic representation: E1_int * base^E2_int
                return (1.0, ("SFP", E1_int, E2_int))
            else:
                try:
                    val_of_base_E2_term = base ** E2_int
                    new_final_exponent = E1_int * val_of_base_E2_term
                    return (1.0, new_final_exponent)
                except OverflowError: # Should be rare for Python ints
                    raise OverflowError("Hyper-power int exponent too large for memory (Path 1.1).")

        # Subcase 1.2: Power is (1.0 * SymbolicExponent(...))
        # This is (base^E1_int) ^ (base ^ (Factor_p * base^Exp_p_base))
        elif cmath.isclose(power_coeff, 1.0) and is_symbolic_exponent(power_expon_repr):
            # Power is base^(Factor_p * base^Exp_p_base)
            # This is too complex for current design to further reduce symbolically.
            # Effectively, we cannot take a symbolic exponent and raise base to it easily.
            raise NotImplementedError(f"Raising a base to a nested symbolic power exponent ({power_expon_repr}) is not supported.")

        # Subcase 1.3: Power is (C_p * base^E2_int) or (C_p, 0) [i.e. a number]
        # This means power_vt evaluates to a numerical p_numeric
        # We calculate (base^E1_int) ^ p_numeric
        else: # power_coeff is not 1.0 OR power_expon_repr is not int (but not SFP if caught above)
            try:
                if is_symbolic_exponent(power_expon_repr): # Should have been caught if power_coeff was 1.0
                    raise EngineLogicError("Symbolic exponent with non-unit coeff in power term.")

                if not isinstance(power_expon_repr, int):
                    raise TypeError("Power exponent must be an integer for evaluation.")
                if power_expon_repr > MAX_E_FOR_DIRECT_BASE_POWER_CALC:
                    raise OverflowError(f"Exponent E_p={power_expon_repr} in power term '{power_vt}' too large for base**E_p evaluation.")
                term_from_E2 = base ** power_expon_repr
                p_numeric = power_coeff * term_from_E2
            except OverflowError:
                raise OverflowError(f"Power term '{power_vt}' (base^{power_expon_repr}) too large to evaluate to a number.")

            # Now we have (base^E1_int) ^ p_numeric
            if cmath.isclose(p_numeric.imag, 0) and math.isclose(p_numeric.real, round(p_numeric.real)):
                p_int = int(round(p_numeric.real))
                try:
                    # Result is base ^ (E1_int * p_int)
                    new_expon = E1_int * p_int
                    return (1.0, new_expon)
                except OverflowError: # E1_int * p_int too large
                    raise OverflowError("Resulting exponent E1*p_int too large (Path 1.3).")
            else: # p_numeric is float/complex
                # Result is (base^E1_int)^p_numeric -> numerically
                try:
                    val_of_base_term = base ** E1_int # This is base^E1_int
                    final_result_numeric = val_of_base_term ** p_numeric
                    return (final_result_numeric, 0)
                except OverflowError:
                    raise OverflowError(f"Result of (base^{E1_int}) ^ '{p_numeric}' is too large.")

    # Case 2: Base is general (C_b * base^E1_int) or (C_b * base^SymbolicExp)
    # For now, assume base_expon_repr is int.
    if is_symbolic_exponent(base_expon_repr):
        raise NotImplementedError("General power with symbolic base exponent not supported.")
    if not isinstance(base_expon_repr, int):
        raise TypeError("Base exponent must be an integer for evaluation.")
    E1_int_base = base_expon_repr # Known to be int here

    # Evaluate power_vt to p_numeric
    try:
        if is_symbolic_exponent(power_expon_repr):
            raise EngineLogicError("Cannot evaluate symbolic power exponent to numeric for general base.")
        if not isinstance(power_expon_repr, int):
            raise TypeError("Power exponent must be an integer for evaluation.")
        if power_expon_repr > MAX_E_FOR_DIRECT_BASE_POWER_CALC:
            raise OverflowError(f"Exponent E_p={power_expon_repr} in power term '{power_vt}' too large for base**E_p evaluation.")
        term_from_E2_power = base ** power_expon_repr
        p_numeric = power_coeff * term_from_E2_power
    except OverflowError:
        raise OverflowError(f"Power term '{power_vt}' (base^{power_expon_repr}) too large to evaluate to a number.")

    # Now (base_coeff * base^E1_int_base) ^ p_numeric
    if cmath.isclose(p_numeric.imag, 0) and math.isclose(p_numeric.real, round(p_numeric.real)):
        p_int = int(round(p_numeric.real))
        try:
            new_coeff = base_coeff ** p_int
            new_expon = E1_int_base * p_int
            return (new_coeff, new_expon)
        except (OverflowError, ValueError):
            pass # Fallback

    try:
        val_of_base_term = base_coeff * (base ** E1_int_base)
        final_result_numeric = val_of_base_term ** p_numeric
        return (final_result_numeric, 0)
    except OverflowError:
        raise OverflowError(f"Result of '{base_vt}' ^ '{p_numeric}' is too large.")

def simplify_value(val: ValueTuple, base: int) -> ValueTuple:
    coeff, expon_repr = val
    if is_symbolic_exponent(expon_repr): return val # Cannot simplify symbolic exponents further here

    # Standard simplification for integer exponents
    if not isinstance(expon_repr, int):
        raise TypeError("Exponent must be an integer for simplification.")
    expon = expon_repr
    if base <= 1 or cmath.isclose(coeff, 0j) or not cmath.isclose(coeff.imag, 0):
        return val
    if coeff.real > 0:
        try:
            log_val = math.log(coeff.real, base)
            if math.isclose(log_val, round(log_val)):
                power_to_absorb = int(round(log_val))
                if abs(power_to_absorb) < 2000:
                    absorb_val = base ** power_to_absorb
                    if cmath.isclose(coeff / absorb_val, 1.0):
                        return (1.0, expon + power_to_absorb)
        except (ValueError, OverflowError):
            pass
    return (coeff, expon) # Return with original int exponent
