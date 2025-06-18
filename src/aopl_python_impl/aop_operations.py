# aopl_python_impl/aop_operations.py
import cmath, math, decimal
from decimal import Decimal, getcontext
from typing import Union, List
from .aop_value import AoPValue, AoPTerm, PracticalLimitError

getcontext().prec = 100

def simplify_value(val: AoPValue, base: int = 10) -> AoPValue:
    if not val.terms: return val
    processed_terms = [AoPTerm(term.coeff, simplify_value(term.exponent, base) if isinstance(term.exponent, AoPValue) else term.exponent) for term in val.terms]
    current_val = AoPValue(processed_terms)
    absorbed_terms = []
    for term in current_val.terms:
        coeff, exp = term.coeff, term.exponent
        if cmath.isclose(coeff.imag, 0) and coeff.real > 0 and not cmath.isclose(coeff.real, 1.0):
            try:
                log_coeff = (Decimal(coeff.real).log10() / Decimal(base).log10())
                if abs(log_coeff - log_coeff.to_integral_value(rounding=decimal.ROUND_HALF_UP)) < Decimal("1e-50"):
                    log_c = log_coeff.to_integral_value(rounding=decimal.ROUND_HALF_UP)
                    exp_aop = exp if isinstance(exp, AoPValue) else AoPValue.from_number(exp)
                    new_exp = add_values(AoPValue.from_number(log_c), exp_aop, base)
                    absorbed_terms.append(AoPTerm(1.0, new_exp))
                    continue
            except Exception: pass
        absorbed_terms.append(term)
    current_val = AoPValue(absorbed_terms)
    if len(current_val.terms) > 1:
        grouped = {}; [grouped.setdefault(repr(t.exponent), []).append(t) for t in current_val.terms]
        current_val = AoPValue([AoPTerm(sum(t.coeff for t in term_list), term_list[0].exponent) for term_list in grouped.values() if not cmath.isclose(sum(t.coeff for t in term_list), 0)])
    try:
        if len(current_val.terms) > 1 or (len(current_val.terms) == 1 and cmath.isclose(current_val.terms[0].coeff, 1.0)):
            num = current_val.to_numerical(base)
            if cmath.isclose(num.imag, 0) and num.real > 0:
                log_val = (Decimal(num.real).log10() / Decimal(base).log10())
                if abs(log_val - log_val.to_integral_value(rounding=decimal.ROUND_HALF_UP)) < Decimal("1e-50"):
                    return AoPValue([AoPTerm(1.0, log_val.to_integral_value(rounding=decimal.ROUND_HALF_UP))])
    except Exception: pass
    return current_val

def add_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return simplify_value(AoPValue(v1.terms + v2.terms), base)

def multiply_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    new_terms: List[AoPTerm] = []
    for t1 in v1.terms:
        for t2 in v2.terms:
            new_coeff = t1.coeff * t2.coeff
            exp1, exp2 = t1.exponent, t2.exponent
            if isinstance(exp1, AoPValue) or isinstance(exp2, AoPValue):
                exp1_aop = exp1 if isinstance(exp1, AoPValue) else AoPValue.from_number(exp1)
                exp2_aop = exp2 if isinstance(exp2, AoPValue) else AoPValue.from_number(exp2)
                new_exponent = add_values(exp1_aop, exp2_aop, base)
            else:
                new_exponent = complex(exp1) + complex(exp2)
            new_terms.append(AoPTerm(new_coeff, new_exponent))
    return simplify_value(AoPValue(new_terms), base)

def power_value(base_val: AoPValue, power_val: AoPValue, base: int) -> AoPValue:
    s_base, s_power = simplify_value(base_val, base), simplify_value(power_val, base)
    if len(s_base.terms) != 1: raise NotImplementedError("Power of a sum is not supported.")
    base_term = s_base.terms[0]
    is_simple_scalar = (len(s_power.terms) == 1 and isinstance(s_power.terms[0].exponent, (int,float,Decimal,complex)) and complex(s_power.terms[0].exponent) == 0)
    if is_simple_scalar:
        power_num = complex(s_power.terms[0].coeff)
        try:
            new_coeff = base_term.coeff ** power_num
            base_exp = base_term.exponent
            if isinstance(base_exp, AoPValue): new_exp = multiply_values(base_exp, AoPValue.from_number(power_num), base)
            else: new_exp = complex(base_exp) * power_num
            return simplify_value(AoPValue([AoPTerm(new_coeff, new_exp)]), base)
        except (OverflowError, decimal.InvalidOperation): pass
    if not cmath.isclose(base_term.coeff, 1.0):
        if not cmath.isclose(base_term.coeff.imag, 0) or base_term.coeff.real <= 0: raise NotImplementedError("Complex/non-positive coeffs not supported for symbolic powers.")
        log_coeff = (Decimal(str(base_term.coeff.real)).log10() / Decimal(str(base)).log10())
        coeff_part = multiply_values(AoPValue.from_number(log_coeff), s_power, base)
    else: coeff_part = AoPValue()
    base_exp_aop = base_term.exponent if isinstance(base_term.exponent, AoPValue) else AoPValue.from_number(base_term.exponent)
    exp_part = multiply_values(base_exp_aop, s_power, base)
    final_exponent = add_values(coeff_part, exp_part, base)
    return simplify_value(AoPValue([AoPTerm(1.0, final_exponent)]), base)

def subtract_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return simplify_value(AoPValue(v1.terms + [AoPTerm(-t.coeff, t.exponent) for t in v2.terms]), base)

def divide_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return multiply_values(v1, power_value(v2, AoPValue.from_number(-1), base), base)
