# aopl_python_impl/aop_operations.py
import cmath, math
from decimal import Decimal, getcontext
from typing import Union, List
from .aop_value import AoPValue, AoPTerm, PracticalLimitError

getcontext().prec = 100

def simplify_value(val: AoPValue, base: int = 10) -> AoPValue:
    """
    Simplifies an AoPValue to its canonical form using a safe, multi-stage pipeline.
    This is the definitive simplification engine for the calculator.
    """
    if not val.terms: return val

    # Stage 1: Recursive Simplification of Exponents (Top-down)
    processed_terms = []
    for term in val.terms:
        new_exp = term.exponent
        if isinstance(new_exp, AoPValue):
            new_exp = simplify_value(new_exp, base) # Recursion is safe here
        processed_terms.append(AoPTerm(term.coeff, new_exp))
    current_val = AoPValue(processed_terms)

    # Stage 2: Coefficient Absorption (e.g., 10*a^k -> a^(1+k))
    absorbed_terms = []
    for term in current_val.terms:
        coeff, exp = term.coeff, term.exponent
        if cmath.isclose(coeff.imag, 0) and coeff.real > 0 and cmath.isclose(coeff.real, round(coeff.real)):
            coeff_int = int(round(coeff.real))
            if coeff_int != 1:
                try:
                    coeff_log = math.log(coeff_int, base)
                    if cmath.isclose(coeff_log, round(coeff_log)):
                        # Coeff is a power of the base, so we can absorb it.
                        exp_aop = exp if isinstance(exp, AoPValue) else AoPValue.from_number(exp)
                        coeff_aop = AoPValue.from_number(int(round(coeff_log)))
                        new_exp_aop = add_values(coeff_aop, exp_aop, base) # add_values no longer simplifies
                        absorbed_terms.append(AoPTerm(1.0, simplify_value(new_exp_aop, base))) # Re-simplify the new exponent
                        continue
                except (ValueError, OverflowError): pass
        absorbed_terms.append(term)
    current_val = AoPValue(absorbed_terms)

    # Stage 3: Combine like terms (e.g., a+a -> 2a)
    if len(current_val.terms) > 1:
        grouped = {}
        for term in current_val.terms:
            key = repr(term.exponent)
            grouped.setdefault(key, []).append(term)
        current_val = AoPValue([AoPTerm(sum(t.coeff for t in term_list), term_list[0].exponent) for term_list in grouped.values() if not cmath.isclose(sum(t.coeff for t in term_list), 0)])

    # Stage 4: Final Conversion Checks
    # Heuristic for derived values (e.g., 2^j)
    if len(current_val.terms) == 1:
        term = current_val.terms[0]
        if not cmath.isclose(term.coeff.imag, 0) or not cmath.isclose(term.coeff.real, round(term.coeff.real)):
            try: return AoPValue.from_number(current_val.to_numerical(base))
            except Exception: pass

    # Check for letter form (e.g., a*b -> c or j^j -> a^k)
    try:
        num = current_val.to_numerical(base)
        if cmath.isclose(num.imag, 0) and num.real > 0:
            log_val = math.log(num.real, base)
            if cmath.isclose(log_val, round(log_val)):
                return AoPValue([AoPTerm(1.0, int(round(log_val)))])
    except Exception: pass

    return current_val

def add_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue: return AoPValue(v1.terms + v2.terms)
def subtract_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue: return AoPValue(v1.terms + [AoPTerm(-t.coeff, t.exponent) for t in v2.terms])

def multiply_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    new_terms: List[AoPTerm] = []
    for t1 in v1.terms:
        for t2 in v2.terms:
            new_coeff = t1.coeff * t2.coeff
            exp1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_term(AoPTerm(1.0, t1.exponent))
            exp2_aop = t2.exponent if isinstance(t2.exponent, AoPValue) else AoPValue.from_term(AoPTerm(1.0, t2.exponent))
            new_exp_aop = add_values(exp1_aop, exp2_aop, base)
            if len(new_exp_aop.terms) == 1:
                new_terms.append(AoPTerm(new_coeff, new_exp_aop.terms[0].exponent))
            else:
                new_terms.append(AoPTerm(new_coeff, new_exp_aop))
    return AoPValue(new_terms)

def power_value(base_val: AoPValue, power_val: AoPValue, base: int) -> AoPValue:
    if len(base_val.terms) != 1: raise NotImplementedError("Power of a sum is not supported.")
    base_term = base_val.terms[0]
    try:
        power_num = power_val.to_numerical(base)
        new_coeff = base_term.coeff ** power_num
        if isinstance(base_term.exponent, AoPValue):
            new_exp = multiply_values(AoPValue.from_number(power_num.real if isinstance(power_num, complex) else power_num), base_term.exponent, base)
        else:
            base_exp = float(base_term.exponent) if isinstance(base_term.exponent, (Decimal, int, float)) else float(complex(base_term.exponent).real)
            power_exp = float(power_num.real) if isinstance(power_num, complex) else float(power_num)
            new_exp = Decimal(base_exp) * Decimal(power_exp)
        return AoPValue.from_term(AoPTerm(new_coeff, new_exp))
    except (OverflowError, PracticalLimitError):
        if isinstance(base_term.exponent, AoPValue): raise NotImplementedError("Recursive base to recursive power not supported.")
        log_base_val = (Decimal(str(base_term.coeff.real)).log10() / Decimal(str(base)).log10()) + Decimal(str(float(base_term.exponent) if isinstance(base_term.exponent, (Decimal, int, float)) else float(complex(base_term.exponent).real)))
        new_exponent = multiply_values(AoPValue.from_number(log_base_val), power_val, base)
        return AoPValue.from_term(AoPTerm(1.0, new_exponent))

def divide_values(v1: AoPValue, v2: AoPValue, base: int) -> AoPValue:
    if len(v2.terms) == 1 and cmath.isclose(v2.terms[0].coeff, 0): raise ZeroDivisionError("Division by zero.")
    return multiply_values(v1, power_value(v2, AoPValue.from_number(-1), base))
