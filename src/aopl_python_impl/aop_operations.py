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
    new_terms: List[AoPTerm] = []
    for t1 in v1.terms:
        for t2 in v2.terms:
            # Check if the term's coefficient and exponent can be converted to a simple number
            s1 = None
            s2 = None
            try:
                if cmath.isclose(t1.coeff.imag, 0) and isinstance(t1.exponent, (int, float, Decimal, complex)) and cmath.isclose(complex(t1.exponent).imag, 0):
                    s1 = t1.coeff.real * (base ** complex(t1.exponent).real)
            except OverflowError:
                s1 = None
            try:
                if cmath.isclose(t2.coeff.imag, 0) and isinstance(t2.exponent, (int, float, Decimal, complex)) and cmath.isclose(complex(t2.exponent).imag, 0):
                    s2 = t2.coeff.real * (base ** complex(t2.exponent).real)
            except OverflowError:
                s2 = None

            if s1 is not None and len(v1.terms) == 1:
                new_terms.extend(scalar_multiply(s1, v2, base).terms)
                break
            if s2 is not None and len(v2.terms) == 1:
                new_terms.extend(scalar_multiply(s2, v1, base).terms)
                continue

            new_coeff = t1.coeff * t2.coeff
            exp1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_number(t1.exponent)
            exp2_aop = t2.exponent if isinstance(t2.exponent, AoPValue) else AoPValue.from_number(t2.exponent)
            new_exponent = add_values(exp1_aop, exp2_aop, base)
            new_terms.append(AoPTerm(new_coeff, new_exponent))

        else:
            continue
        break
    return simplify_value(AoPValue(new_terms), base)

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
        power_num = s_power.to_numerical(base)
        new_coeff = base_term.coeff ** power_num
        new_exp = complex(base_term.exponent) * power_num

        # This is the key change: if the result is too big, it will raise an OverflowError here
        # which is caught below, triggering the symbolic path.
        if not cmath.isfinite(new_coeff) or not cmath.isfinite(new_exp): raise OverflowError("Numerical power result is not finite")
        logging.debug(f"Numeric power success. Result: c={new_coeff}, e={new_exp}")
        return simplify_value(AoPValue([AoPTerm(new_coeff, new_exp)]), base)
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
