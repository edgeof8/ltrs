# aopl_python_impl/aop_operations.py
import cmath, decimal
from decimal import Decimal
from typing import List, Union, Tuple
from .aop_value import AoPValue, AoPTerm # Keep direct import
from .definitions import PracticalLimitError # Import PracticalLimitError

# Helper function to create terms, potentially simplifying numeric AoPValue exponents
def create_term(coeff: complex, exponent: Union[Decimal, complex, AoPValue], base: int) -> AoPTerm:
    """
    Creates an AoPTerm. If the provided exponent is an AoPValue that
    represents a simple numerical constant (e.g., AoPValue([Term(N,0)])),
    it unwraps it to use the number N directly as the exponent.
    """
    if isinstance(exponent, AoPValue):
        # Check if the AoPValue exponent is a single term representing a number (coeff*base^0)
        if len(exponent.terms) == 1:
            term_exp = exponent.terms[0]
            # Check if this term_exp has a numeric exponent that is zero
            is_simple_numeric_value = False
            if isinstance(term_exp.exponent, (int, float, Decimal, complex)):
                try:
                    if cmath.isclose(complex(term_exp.exponent), 0):
                        is_simple_numeric_value = True
                except TypeError:
                    pass # Not a type that complex() can handle, or not numeric

            if is_simple_numeric_value:
                # The AoPValue 'exponent' represents the number term_exp.coeff.
                # This number should become the actual exponent of the new term.
                value_as_complex = complex(term_exp.coeff)
                if cmath.isclose(value_as_complex.imag, 0):
                    exponent = Decimal(value_as_complex.real)
                else:
                    exponent = value_as_complex # Keep as complex if it has imag part
                # print(f"DEBUG create_term: Simplified AoPValue exponent to numeric: {exponent}") # Optional debug

    return AoPTerm(coeff, exponent)


def simplify_terms_list(terms: List[AoPTerm], base: int) -> List[AoPTerm]:
    # ... (rest of existing simplify_terms_list)
    if not terms: return []
    # Combine terms with the same exponent (including AoPValue exponents if they are identical)
    # For AoPValue exponents, they must be structurally identical to be combined.
    # A robust way is to convert them to a canonical string form for comparison if they are AoPValues.

    # Temporarily, let's make exponent comparison more direct for simplification
    # This might require AoPValue to have a proper __hash__ and __eq__ if used as dict keys directly
    # For now, we'll iterate and combine.

    simplified_dict = {} # Using a dict where key is exponent representation

    for term in terms:
        exp_key: Union[complex, str]
        current_exponent = term.exponent

        if isinstance(current_exponent, AoPValue):
            # For AoPValue exponents, use their string representation (in AOP mode) as a key.
            # This is a pragmatic way to group identical symbolic exponents.
            # Requires a get_letter function, which we don't have here.
            # Fallback: Treat unique AoPValue objects as unique exponents for now,
            # or simplify them if they become numeric.
            try:
                # If AoPValue exponent can be turned into a number, do it for grouping.
                num_exp = current_exponent.to_numerical(base)
                # Check if it's a "simple" number (not too large, not NaN/inf)
                if cmath.isfinite(num_exp) and abs(num_exp.real) < 1e18 and abs(num_exp.imag) < 1e18 : # Heuristic
                    exp_key = num_exp
                    current_exponent = num_exp # Use the simplified numeric exponent
                else: # Treat as symbolic, use object ID or a hash if AoPValue implements it
                    exp_key = id(current_exponent) # Not ideal, but a placeholder
            except (OverflowError, PracticalLimitError, NotImplementedError): # Could fail if symbolic
                exp_key = id(current_exponent) # Fallback for non-numerical AoPValues
        else: # Numeric exponent (Decimal or complex)
            exp_key = complex(current_exponent) # Normalize to complex for dict key

        # Update the term's exponent if it was simplified from AoPValue to numeric
        term_to_add = AoPTerm(term.coeff, current_exponent)

        if exp_key in simplified_dict:
            simplified_dict[exp_key].coeff += term_to_add.coeff
        else:
            simplified_dict[exp_key] = term_to_add

    # Filter out terms with zero coefficient and reconstruct the list
    new_terms = [t for t in simplified_dict.values() if not cmath.isclose(t.coeff, 0)]

    # Sort by exponent (descending magnitude for numeric, then perhaps string for symbolic)
    # This sorting is complex with mixed exponent types. A simple sort:
    def sort_key(t: AoPTerm):
        if isinstance(t.exponent, AoPValue):
            # Try to get a representative numeric value for sorting, or large fallback
            try: return -abs(t.exponent.to_numerical(base).real if t.exponent.terms else float('-inf'))
            except: return float('-inf') # Place complex/uncomputable AoPValue exponents first/last
        else: # Numeric
            return -abs(complex(t.exponent).real) # Sort by real part of exponent magnitude

    new_terms.sort(key=sort_key)
    return new_terms


def simplify_value(value: AoPValue, base: int) -> AoPValue:
    simplified_terms = simplify_terms_list(value.terms, base)
    return AoPValue(simplified_terms)

# Addition
def add_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    return simplify_value(AoPValue(op1.terms + op2.terms), base)

# Subtraction
def subtract_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    neg_op2_terms = [create_term(-t.coeff, t.exponent, base) for t in op2.terms]
    return simplify_value(AoPValue(op1.terms + neg_op2_terms), base)

# Multiplication
def multiply_terms(t1: AoPTerm, t2: AoPTerm, base: int) -> List[AoPTerm]:
    new_coeff = t1.coeff * t2.coeff
    if cmath.isclose(new_coeff, 0): return []

    exp1_val = t1.exponent
    exp2_val = t2.exponent

    # Handle exponents. If one is AoPValue and other is numeric, add carefully.
    final_exp: Union[Decimal, complex, AoPValue]

    if isinstance(exp1_val, AoPValue) and isinstance(exp2_val, AoPValue):
        final_exp = add_values(exp1_val, exp2_val, base)
    elif isinstance(exp1_val, AoPValue): # exp2_val is numeric
        final_exp = add_values(exp1_val, AoPValue.from_number(complex(exp2_val)), base)
    elif isinstance(exp2_val, AoPValue): # exp1_val is numeric
        final_exp = add_values(AoPValue.from_number(complex(exp1_val)), exp2_val, base)
    else: # Both numeric
        numeric_sum = complex(exp1_val) + complex(exp2_val)
        if cmath.isclose(numeric_sum.imag, 0):
            final_exp = Decimal(numeric_sum.real)
        else:
            final_exp = numeric_sum

    return [create_term(new_coeff, final_exp, base)]

def multiply_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    if not op1.terms or not op2.terms: return AoPValue()
    new_terms: List[AoPTerm] = []
    for t1 in op1.terms:
        for t2 in op2.terms:
            new_terms.extend(multiply_terms(t1, t2, base))
    return simplify_value(AoPValue(new_terms), base)

# Division (simplified)
def divide_values(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    if not op2.terms: raise ZeroDivisionError("Division by AoPValue zero.")

    # Simple case: op2 is a single, non-zero numeric constant
    if len(op2.terms) == 1 and op2.terms[0].is_numeric_exponent_zero():
        divisor_coeff = op2.terms[0].coeff
        if cmath.isclose(divisor_coeff, 0): raise ZeroDivisionError("Division by zero coefficient.")
        inv_coeff = 1.0 / divisor_coeff
        new_terms = [create_term(t.coeff * inv_coeff, t.exponent, base) for t in op1.terms]
        return simplify_value(AoPValue(new_terms), base)

    # General case: X / Y = X * Y^-1. Power -1 can be complex.
    # For now, if op2 is not a simple number, try numerical evaluation.
    try:
        num1 = op1.to_numerical(base)
        num2 = op2.to_numerical(base)
        if cmath.isclose(num2, 0): raise ZeroDivisionError("Numerical division by zero.")
        return AoPValue.from_number(num1 / num2)
    except (OverflowError, PracticalLimitError, NotImplementedError) as e:
        raise NotImplementedError(f"Symbolic division for {op1!r} / {op2!r} not fully implemented or failed: {e}")


# Power
def power_value(op1: AoPValue, op2: AoPValue, base: int) -> AoPValue:
    if not op1.terms: return AoPValue() # 0^Y is 0 (unless Y=0, then 1; or Y<0, then error)

    # Case 1: op2 is a simple numeric constant
    if len(op2.terms) == 1 and op2.terms[0].is_numeric_exponent_zero():
        pow_val_complex = complex(op2.terms[0].coeff)

        if cmath.isclose(pow_val_complex, 0): return AoPValue.from_number(1) # X^0 = 1
        if cmath.isclose(pow_val_complex, 1): return op1 # X^1 = X

        # If op1 is also a simple numeric constant C1, result is C1^pow_val
        if len(op1.terms) == 1 and op1.terms[0].is_numeric_exponent_zero():
            base_val_complex = complex(op1.terms[0].coeff)
            try:
                # Check for 0^negative_power
                if cmath.isclose(base_val_complex,0) and pow_val_complex.real < 0 and cmath.isclose(pow_val_complex.imag,0):
                    raise ZeroDivisionError("0 raised to a negative power.")
                result_val = base_val_complex ** pow_val_complex
                if not cmath.isfinite(result_val): raise OverflowError("Result of const^const is not finite.")
                return AoPValue.from_number(result_val)
            except (OverflowError, ZeroDivisionError) as e_pow:
                 raise OverflowError(f"Error in const^const power: {e_pow}")


        # op1 is symbolic C1*a^E1, op2 is numeric N
        # Result is (C1*a^E1)^N = C1^N * a^(E1*N)
        new_terms = []
        for t1 in op1.terms:
            try:
                term_coeff_pow_N = t1.coeff ** pow_val_complex
                if not cmath.isfinite(term_coeff_pow_N): raise OverflowError("Coeff^N not finite")
            except OverflowError as e_coeff_pow:
                 raise OverflowError(f"Error in (coeff^N) for power: {e_coeff_pow}")


            exp_E1 = t1.exponent
            # E1 * N
            if isinstance(exp_E1, AoPValue):
                term_exp_mul_N = multiply_values(exp_E1, AoPValue.from_number(pow_val_complex), base)
            else: # E1 is numeric
                numeric_prod = complex(exp_E1) * pow_val_complex
                if cmath.isclose(numeric_prod.imag, 0):
                    term_exp_mul_N = Decimal(numeric_prod.real)
                else:
                    term_exp_mul_N = numeric_prod

            new_terms.append(create_term(term_coeff_pow_N, term_exp_mul_N, base))
        return simplify_value(AoPValue(new_terms), base)

    # Case 2: op1 is 'a' (base value: 1*a^1)
    if len(op1.terms) == 1 and op1.terms[0].coeff == 1 and \
       isinstance(op1.terms[0].exponent, (int,float,Decimal,complex)) and \
       cmath.isclose(complex(op1.terms[0].exponent), 1):
        # op1 is 'a', result is a^op2
        return AoPValue([create_term(coeff=1, exponent=op2, base=base)])

    # Fallback: try numerical evaluation for X^Y if not covered above
    try:
        num1 = op1.to_numerical(base)
        num2 = op2.to_numerical(base)
        # Check for 0^negative_power or 0^0 if op2 is complex with real part <=0
        if cmath.isclose(num1,0):
            if cmath.isclose(num2,0): # 0^0 = 1
                return AoPValue.from_number(1)
            if num2.real < 0 and cmath.isclose(num2.imag,0): # 0 to negative real power
                raise ZeroDivisionError("Numerical 0 raised to a negative power.")

        result = num1 ** num2
        if not cmath.isfinite(result):
            raise OverflowError("Numerical result of power is not finite.")
        return AoPValue.from_number(result)
    except (OverflowError, PracticalLimitError, ZeroDivisionError, NotImplementedError) as e_num:
        # Symbolic fallback for (C1*a^E1) ^ op2
        # Result is base ^ ( (log_base C1 + E1) * op2 )
        if len(op1.terms) == 1:
            t1 = op1.terms[0]
            log_base_C1_val = cmath.log(t1.coeff, base) if not cmath.isclose(t1.coeff,0) else float('-inf') # Avoid log(0)
            if log_base_C1_val == float('-inf') and not isinstance(t1.exponent, AoPValue) and complex(t1.exponent).real <= 0 : # 0^(positive power)
                 return AoPValue.from_number(0) # 0^X = 0 if X > 0

            log_base_C1_aop = AoPValue.from_number(log_base_C1_val)

            E1_aop: AoPValue
            if isinstance(t1.exponent, AoPValue):
                E1_aop = t1.exponent
            else: # E1 is numeric
                E1_aop = AoPValue.from_number(complex(t1.exponent))

            log_base_op1 = add_values(log_base_C1_aop, E1_aop, base)

            new_exponent_for_final_a = multiply_values(log_base_op1, op2, base)
            return AoPValue([create_term(coeff=1, exponent=new_exponent_for_final_a, base=base)])

        raise AoPError(f"Cannot evaluate {op1!r}^{op2!r} symbolically or numerically: {e_num}")

# Helper to check if an AoPValue represents a single numeric constant (for power_value mainly)
# This is implicitly used by checking len(op.terms)==1 and op.terms[0].is_numeric_exponent_zero()
