# aopl_python_impl/aop_operations.py
import cmath, math, decimal, logging
from decimal import Decimal, getcontext
from typing import Union, List, Dict, Tuple
from .aop_value import AoPValue, AoPTerm, PracticalLimitError

getcontext().prec = 200

def simplify_value(val: AoPValue, base: int = 10) -> AoPValue:
    # ... (This function is already correct)
    logging.debug(f"simplify_value: INPUT = {val!r}") # Changed log prefix for clarity
    if not val.terms: return AoPValue() # Return empty AoPValue for "0" or empty input

    # Step 1: Recursively simplify exponents within all terms
    logging.debug(f"simplify_value: Step 1 - Simplifying exponents within terms...")
    processed_terms = [AoPTerm(term.coeff, simplify_value(term.exponent, base) if isinstance(term.exponent, AoPValue) else term.exponent) for term in val.terms]
    current_val = AoPValue(processed_terms)
    logging.debug(f"simplify_value: After Step 1 (exp simp) = {current_val!r}")

    # Step 2: Attempt to numerically sum terms if all are simple numbers or can be evaluated
    if len(current_val.terms) > 1:
        logging.debug(f"simplify_value: Step 2 - Attempting numerical sum for {len(current_val.terms)} terms.")
        can_attempt_numerical_sum = all(
            not (
                isinstance(term.exponent, AoPValue) and (
                    len(term.exponent.terms) > 1 or
                    (len(term.exponent.terms) == 1 and (
                        isinstance(term.exponent.terms[0].exponent, AoPValue) or
                        (isinstance(term.exponent.terms[0].exponent, complex) and not cmath.isclose(term.exponent.terms[0].exponent.imag, 0))
                    ))
                )
            )
            for term in current_val.terms
        )
        if can_attempt_numerical_sum:
            try:
                numerical_sum_val = current_val.to_numerical(base) # This sums all terms numerically
                if cmath.isfinite(numerical_sum_val):
                    logging.debug(f"simplify_value: Step 2 - Numerical sum successful: {numerical_sum_val}")
                    current_val = AoPValue([AoPTerm(coeff=numerical_sum_val, exponent=0)])
                else:
                    logging.debug(f"simplify_value: Step 2 - Numerical sum resulted in non-finite value: {numerical_sum_val}.")
            except (PracticalLimitError, TypeError, decimal.InvalidOperation, OverflowError):
                logging.debug("simplify_value: Step 2 - Numerical summation failed (PracticalLimitError/TypeError/DecimalError), proceeding with symbolic sum.")
                pass
        logging.debug(f"simplify_value: After Step 2 (num sum) = {current_val!r}")

    # Step 3: Group terms with identical exponents (symbolic sum)
    if len(current_val.terms) > 1: # Check again, as numerical sum might have reduced it to 1 term
        logging.debug(f"simplify_value: Step 3 - Grouping {len(current_val.terms)} terms symbolically.")
        grouped: Dict[Union[str, Tuple[str, str]], List[AoPTerm]] = {}
        for t in current_val.terms:
            exp_key_obj = t.exponent
            if isinstance(exp_key_obj, AoPValue): exp_key = repr(exp_key_obj) # AoPValues are hashable via repr
            elif isinstance(exp_key_obj, complex): exp_key = (repr(exp_key_obj.real), repr(exp_key_obj.imag))
            else: exp_key = repr(exp_key_obj) # For Decimal, int, float
            grouped.setdefault(exp_key, []).append(t)

        summed_terms: List[AoPTerm] = []
        for term_list in grouped.values():
            total_coeff = sum(t.coeff for t in term_list)
            if not cmath.isclose(total_coeff, 0.0, abs_tol=1e-100):
                summed_terms.append(AoPTerm(total_coeff, term_list[0].exponent))
        current_val = AoPValue(summed_terms)
    logging.debug(f"simplify_value: After Step 3 (sym sum) = {current_val!r}")

    # Step 4: Simplify single term (e.g., coefficient absorption)
    if len(current_val.terms) == 1:
        logging.debug(f"simplify_value: Step 4 - Simplifying single term: {current_val.terms[0]!r}")
        term = current_val.terms[0]
        # Only attempt absorption for positive real coefficients not equal to 1.
        if cmath.isclose(term.coeff.imag, 0) and term.coeff.real > 0 and not cmath.isclose(term.coeff.real, 1.0) and isinstance(term.coeff.real, (float,int,Decimal)):
            try:
                # Use natural log for consistency and to handle arbitrary bases properly
                log_coeff_val = Decimal(str(term.coeff.real)).ln() / Decimal(str(base)).ln() # log_base(coeff)
                logging.debug(f"simplify_value: Step 4 - Term: {term!r}, log_coeff_val: {log_coeff_val}")

                if abs(log_coeff_val - log_coeff_val.to_integral_value(rounding=decimal.ROUND_HALF_UP)) < Decimal("1e-50"): # High precision check
                    coeff_exp_part_val = log_coeff_val.to_integral_value(rounding=decimal.ROUND_HALF_UP)
                    logging.debug(f"simplify_value: Step 4 - Coeff is power of base, exponent part: {coeff_exp_part_val}")
                    if isinstance(term.exponent, (Decimal, complex, int, float)):
                        # Ensure current exponent is treated as Decimal if it's real
                        current_exp_is_complex_real = isinstance(term.exponent, complex) and cmath.isclose(term.exponent.imag, 0)
                        current_exp_val_decimal = Decimal(str(term.exponent.real)) if current_exp_is_complex_real else Decimal(str(term.exponent)) # Convert to Decimal

                        new_exponent_val = current_exp_val_decimal + coeff_exp_part_val
                        current_val = AoPValue([AoPTerm(1.0, new_exponent_val)])
                        logging.debug(f"simplify_value: Step 4 - Absorbed coefficient into simple exponent. New term: {current_val.terms[0]!r}")
                    elif isinstance(term.exponent, AoPValue):
                        # Create an AoPValue for the exponent part derived from the coefficient
                        coeff_exp_aop_val = AoPValue.from_number(coeff_exp_part_val)
                        # Add this to the existing AoPValue exponent
                        new_aoP_exponent = add_values(coeff_exp_aop_val, term.exponent, base)
                        current_val = AoPValue([AoPTerm(1.0, new_aoP_exponent)])
                        logging.debug(f"simplify_value: Step 4 - Absorbed coefficient into AoPValue exponent. New exponent obj: {new_aoP_exponent!r}, New term: {current_val.terms[0]!r}")
                    else:
                        logging.debug(f"simplify_value: Step 4 - Current exponent {term.exponent!r} type not suitable for absorption.")
                else:
                    logging.debug(f"simplify_value: Step 4 - log_coeff_val not integer, no absorption.")
            except Exception as e:
                logging.debug(f"simplify_value: Step 4 - Error during coeff absorption for term {term!r}: {e}")
                pass
    logging.debug(f"simplify_value: FINAL RETURN = {current_val!r}")
    return current_val

def add_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return simplify_value(AoPValue(v1.terms + v2.terms), base)

def scalar_multiply(scalar: complex, val: AoPValue, base: int = 10) -> AoPValue:
    if cmath.isclose(scalar, 0): return AoPValue()
    if cmath.isclose(scalar, 1): return val
    new_terms = [AoPTerm(term.coeff * scalar, term.exponent) for term in val.terms]
    return simplify_value(AoPValue(new_terms), base)

def multiply_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    # --- FINAL ARCHITECTURAL FIX ---
    # The premature scalar optimization is the root of several deep bugs
    # related to numerical underflow and symbolic representation.
    # Removing it ensures all multiplications are handled by the robust
    # term-by-term symbolic path, which is the correct approach for a CAS.
    new_terms: List[AoPTerm] = []
    for t1 in v1.terms:
        for t2 in v2.terms:
            new_coeff = t1.coeff * t2.coeff
            exp1_aop = t1.exponent if isinstance(t1.exponent, AoPValue) else AoPValue.from_number(t1.exponent)
            exp2_aop = t2.exponent if isinstance(t2.exponent, AoPValue) else AoPValue.from_number(t2.exponent)
            new_exponent = add_values(exp1_aop, exp2_aop, base)
            new_terms.append(AoPTerm(new_coeff, new_exponent))
    return simplify_value(AoPValue(new_terms), base)

def power_value(base_val: AoPValue, power_val: AoPValue, base: int) -> AoPValue:
    s_base, s_power = simplify_value(base_val, base), simplify_value(power_val, base)

    # --- FINAL FIX: Explicitly forbid power of a sum ---
    # This check was missing, leading to overflow instead of a clean error.
    if len(s_base.terms) > 1:
        raise NotImplementedError("Power of a sum is not supported. Use parentheses to clarify intent, e.g., (a+b)^c.")

    # Handle the case of a single term base, which might be zero.
    if not s_base.terms: # Base is effectively zero
        try:
            power_num = s_power.to_numerical(base)
            if power_num.real > 0:
                return AoPValue() # 0 to a positive power is 0
            else:
                # 0 to a negative or zero power is undefined/infinity
                raise ZeroDivisionError("0.0 cannot be raised to a negative or zero power.")
        except PracticalLimitError:
            # If the power is symbolic, we can't determine its sign.
            raise NotImplementedError("Cannot raise zero to a symbolic power.")

    base_term = s_base.terms[0]

    if isinstance(base_term.exponent, AoPValue):
        return _power_symbolic(base_term, s_power, base)

    try:
        power_num_complex = s_power.to_numerical(base)
        new_coeff_val = base_term.coeff ** power_num_complex
        base_exp_num = complex(base_term.exponent)
        new_exp_val = base_exp_num * power_num_complex

        if not cmath.isfinite(new_coeff_val) or not cmath.isfinite(new_exp_val):
            raise OverflowError("Numerical power result is not finite")
        return simplify_value(AoPValue([AoPTerm(new_coeff_val, new_exp_val)]), base)
    except (OverflowError, PracticalLimitError, ZeroDivisionError):
        return _power_symbolic(base_term, s_power, base)

def _power_symbolic(base_term: AoPTerm, power_val: AoPValue, base: int) -> AoPValue:
    # ... (This function is already correct)
    logging.debug(f"Symbolic Power: base_term={base_term!r}, power_val={power_val!r}")
    log_coeff_val = 0
    if not cmath.isclose(base_term.coeff, 1.0):
        if cmath.isclose(base_term.coeff.imag, 0) and base_term.coeff.real > 0:
             log_coeff_val = (Decimal(str(base_term.coeff.real)).ln() / Decimal(str(base)).ln())
        else:
            # Handle complex coefficients logarithmically
            log_coeff_val = cmath.log(base_term.coeff) / math.log(base)

    base_exp = base_term.exponent
    if isinstance(base_exp, AoPValue):
        logging.debug("Symbolic Path: Tower of Power case")
        log_part = scalar_multiply(complex(log_coeff_val), power_val, base)
        exp_part = multiply_values(base_exp, power_val, base)
        final_exponent = add_values(log_part, exp_part, base)
    else:
        logging.debug("Symbolic Path: Simple exponent case")
        combined_exp_scalar = complex(log_coeff_val) + complex(base_exp)
        final_exponent = scalar_multiply(combined_exp_scalar, power_val, base)

    logging.debug(f"Symbolic power result exponent: {final_exponent!r}")
    return simplify_value(AoPValue([AoPTerm(1.0, final_exponent)]), base)


def subtract_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    return simplify_value(AoPValue(v1.terms + [AoPTerm(-t.coeff, t.exponent) for t in v2.terms]), base)

def divide_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    try:
        v2_num = v2.to_numerical(base)
        if cmath.isclose(v2_num, 0):
            raise ZeroDivisionError("Division by zero.")
    except PracticalLimitError:
        pass
    return multiply_values(v1, power_value(v2, AoPValue.from_number(-1), base), base)

def equals_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue:
    try:
        num1 = v1.to_numerical(base)
        num2 = v2.to_numerical(base)
        if cmath.isclose(num1, num2, rel_tol=1e-9, abs_tol=1e-12):
            return AoPValue.from_number(1)
        else:
            return AoPValue.from_number(0)
    except PracticalLimitError:
        s1 = simplify_value(v1, base)
        s2 = simplify_value(v2, base)
        if repr(s1) == repr(s2):
             return AoPValue.from_number(1)
        return AoPValue.from_number(0)
    except Exception as e:
        logging.error(f"Error during equality comparison: {e}")
        return AoPValue.from_number(0)
