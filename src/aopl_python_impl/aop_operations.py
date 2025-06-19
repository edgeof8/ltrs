# aopl_python_impl/aop_operations.py
import cmath, math, decimal, logging
from decimal import Decimal, getcontext
from typing import Union, List
from .aop_value import AoPValue, AoPTerm, PracticalLimitError

getcontext().prec = 200

def simplify_value(val: AoPValue, base: int = 10) -> AoPValue:
    logging.debug(f"Simplifying: {val!r}")
    if not val.terms: return val
    processed_terms = [AoPTerm(term.coeff, simplify_value(term.exponent, base) if isinstance(term.exponent, AoPValue) else term.exponent) for term in val.terms]
    current_val = AoPValue(processed_terms)

    if len(current_val.terms) == 1:
        term = current_val.terms[0]
        if cmath.isclose(term.coeff.imag, 0) and term.coeff.real > 0 and not cmath.isclose(term.coeff.real, 1.0):
            try:
                log_coeff_val = (Decimal(str(term.coeff.real))).log10() / Decimal(base).log10()
                if abs(log_coeff_val - log_coeff_val.to_integral_value(rounding=decimal.ROUND_HALF_UP)) < Decimal("1e-100"):
                    new_exp_part = AoPValue.from_number(log_coeff_val.to_integral_value(rounding=decimal.ROUND_HALF_UP))
                    old_exp_part = term.exponent if isinstance(term.exponent, AoPValue) else AoPValue.from_number(term.exponent)
                    final_exp = add_values(new_exp_part, old_exp_part, base)
                    return AoPValue([AoPTerm(1.0, final_exp.to_simple_number() or final_exp)])
            except Exception:
                pass

    if len(current_val.terms) > 1:
        grouped = {}; [grouped.setdefault(repr(t.exponent), []).append(t) for t in current_val.terms]
        current_val = AoPValue([AoPTerm(sum(t.coeff for t in term_list), term_list[0].exponent) for term_list in grouped.values() if not cmath.isclose(sum(t.coeff for t in term_list), 0)])

    return current_val

def add_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return simplify_value(AoPValue(v1.terms + v2.terms), base)

def scalar_multiply(scalar: complex, val: AoPValue, base: int = 10) -> AoPValue:
    if cmath.isclose(scalar, 0): return AoPValue()
    if cmath.isclose(scalar, 1): return val
    new_terms = [AoPTerm(term.coeff * scalar, term.exponent) for term in val.terms]
    return AoPValue(new_terms)

def multiply_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    # Optimization: if v1 is a single term that's a scalar
    if len(v1.terms) == 1:
        s1 = _try_term_to_scalar(v1.terms[0], base)
        if s1 is not None:
            return simplify_value(scalar_multiply(s1, v2, base), base)

    # Optimization: if v2 is a single term that's a scalar
    if len(v2.terms) == 1:
        s2 = _try_term_to_scalar(v2.terms[0], base)
        if s2 is not None:
            return simplify_value(scalar_multiply(s2, v1, base), base)

    # General case: term-by-term symbolic multiplication
    new_terms: List[AoPTerm] = []
    for t1 in v1.terms:
        for t2 in v2.terms:
            new_coeff = t1.coeff * t2.coeff
            exp1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_number(t1.exponent)
            exp2_aop = t2.exponent if isinstance(t2.exponent, AoPValue) else AoPValue.from_number(t2.exponent)
            new_exponent = add_values(exp1_aop, exp2_aop, base)
            new_terms.append(AoPTerm(new_coeff, new_exponent))

    return simplify_value(AoPValue(new_terms), base)

def _try_term_to_scalar(term: AoPTerm, base: int) -> Union[complex, None]:
    """Helper to try to convert a single term to a numerical scalar.
       Returns None if it's symbolic, would overflow/underflow in a misleading way, or coeff is complex.
    """
    # Only attempt if coefficient is real for this specific optimization path.
    # Complex coefficients with numeric exponents are handled by the general path or if the other operand is scalar.
    if not cmath.isclose(term.coeff.imag, 0):
        return None
    # Exponent must be a simple number (not AoPValue or complex with imag part)
    if not isinstance(term.exponent, (int, float, Decimal, complex)) or not cmath.isclose(complex(term.exponent).imag, 0):
        return None

    try:
        exp_real = complex(term.exponent).real
        if cmath.isclose(term.coeff, 0): # If coefficient is zero, term is scalar 0
            return 0.0

        # Check for base**exp underflow leading to 0 when it shouldn't for this optimization
        val_base_part = float(base) ** exp_real # Use float for this check, consistent with original scalar attempt

        if cmath.isclose(val_base_part, 0.0) and not cmath.isclose(float(base), 0.0) and not cmath.isclose(term.coeff.real,0.0) :
            return None # Term is not truly zero, avoid scalar path that would make it so.

        scalar_val = term.coeff.real * val_base_part
        if not cmath.isfinite(scalar_val): # Check if product overflowed
             return None
        return scalar_val
    except OverflowError: # Overflow from base ** exp_real
        return None

def power_value(base_val: AoPValue, power_val: AoPValue, base: int) -> AoPValue:
    logging.debug(f"Power: ({base_val!r}) ^ ({power_val!r})")
    s_base, s_power = simplify_value(base_val, base), simplify_value(power_val, base)
    if len(s_base.terms) != 1: raise NotImplementedError("Power of a sum is not supported.")
    base_term = s_base.terms[0]

    # If base's exponent is already symbolic, must use symbolic path to avoid type errors.
    if isinstance(base_term.exponent, AoPValue):
        logging.debug("Base exponent is symbolic, entering symbolic power path directly.")
        return _power_symbolic(base_term, s_power, base)

    # Try numerical path first.
    try:
        power_num_complex = s_power.to_numerical(base) # This returns complex
        new_coeff_val = base_term.coeff ** power_num_complex # Coeff power is usually float/complex based

        # Preserve Decimal precision for exponent if possible
        base_exp_val = base_term.exponent # Should be Decimal or AoPValue

        # Determine the type for power_num for exponent multiplication
        actual_power_for_exp_mult: Union[Decimal, complex]
        if cmath.isclose(power_num_complex.imag, 0):
            # Try to get original Decimal from s_power if it's a simple number that can be Decimal
            try: actual_power_for_exp_mult = s_power.to_decimal(base)
            except (TypeError, PracticalLimitError): # Fallback if s_power is complex, an AoPValue, or too large/small for Decimal
                actual_power_for_exp_mult = Decimal(str(power_num_complex.real))
        else: # Fallback to complex math if base_exp is not Decimal or power_num is complex
            actual_power_for_exp_mult = power_num_complex

        if isinstance(base_exp_val, Decimal) and isinstance(actual_power_for_exp_mult, Decimal):
            new_exp_val = base_exp_val * actual_power_for_exp_mult
        else: # One or both are complex or AoPValue (base_exp_val can be AoPValue that needs .to_numerical())
            new_exp_val = complex(base_exp_val.to_numerical(base) if isinstance(base_exp_val, AoPValue) else base_exp_val) * power_num_complex

        if not cmath.isfinite(new_coeff_val) or not cmath.isfinite(complex(new_exp_val)): raise OverflowError("Numerical power result is not finite")
        logging.debug(f"Numeric power success. Result: c={new_coeff_val}, e={new_exp_val}")
        return simplify_value(AoPValue([AoPTerm(new_coeff_val, new_exp_val)]), base)
    except (OverflowError, PracticalLimitError) as e:
        # If numerical path fails, fall back to symbolic.
        logging.debug(f"Numeric power failed ({type(e).__name__}: {e}). Falling back to symbolic path.")
        return _power_symbolic(base_term, s_power, base)

def _power_symbolic(base_term: AoPTerm, power_val: AoPValue, base: int) -> AoPValue:
    """Symbolic power calculation: (C*base^E)^P = base^(P * (log_base(C) + E))"""
    logging.debug(f"Symbolic Power: base_term={base_term!r}, power_val={power_val!r}")
    log_coeff_val = 0
    if not cmath.isclose(base_term.coeff, 1.0):
        if not cmath.isclose(base_term.coeff.imag, 0) or base_term.coeff.real <= 0: raise NotImplementedError("Complex/non-positive coeffs for symbolic powers.")
        log_coeff_val = (Decimal(str(base_term.coeff.real)).log10() / Decimal(str(base)).log10())

    base_exp = base_term.exponent
    if isinstance(base_exp, AoPValue):
        # Case: Tower of Power, E is symbolic. New exponent = P*log(C) + P*E
        logging.debug("Symbolic Path: Tower of Power case")
        log_part = scalar_multiply(complex(log_coeff_val), power_val, base)
        exp_part = multiply_values(base_exp, power_val, base)
        final_exponent = add_values(log_part, exp_part, base)
    else:
        # Case: E is a simple number. New exponent = P * (log(C) + E)
        logging.debug("Symbolic Path: Simple exponent case")
        combined_exp_scalar = complex(log_coeff_val) + complex(base_exp)
        final_exponent = scalar_multiply(combined_exp_scalar, power_val, base)

    logging.debug(f"Symbolic power result exponent: {final_exponent!r}")
    return simplify_value(AoPValue([AoPTerm(1.0, final_exponent)]), base)

def subtract_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return simplify_value(AoPValue(v1.terms + [AoPTerm(-t.coeff, t.exponent) for t in v2.terms]), base)

def divide_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return multiply_values(v1, power_value(v2, AoPValue.from_number(-1), base), base)
