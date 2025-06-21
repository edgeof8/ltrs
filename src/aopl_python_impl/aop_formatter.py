# aopl_python_impl/aop_formatter.py
import math, cmath, decimal
from decimal import Decimal, getcontext
from typing import Callable, Union
from .aop_value import AoPValue, AoPTerm, PracticalLimitError
from .definitions import OutputFormatMode, EXPONENT_TO_LETTER_MAP # Assuming LETTER_TO_EXPONENT_MAP is not needed here

getcontext().prec = 200 # Ensure high precision for Decimal operations

def _complex_to_str(c: complex, precision: int) -> str:
    # Define a suitable absolute tolerance for checking closeness to zero
    # Increased tolerance slightly as 1e-15 was sometimes too strict for typical float noise
    abs_tol_zero = 1e-14

    if cmath.isclose(c.imag, 0, abs_tol=abs_tol_zero):
        real_part = c.real
        # For real part, check if it's an integer using a relative tolerance as well
        if cmath.isclose(real_part, round(real_part), rel_tol=1e-9, abs_tol=abs_tol_zero):
            return str(int(round(real_part)))
        return f"{real_part:.{precision}g}".rstrip('0').rstrip('.')

    # Check if the entire complex number is close to 0 (e.g., 0+0j)
    if cmath.isclose(c.real, 0, abs_tol=abs_tol_zero) and cmath.isclose(c.imag, 0, abs_tol=abs_tol_zero):
        return "0"

    if cmath.isclose(c.real, 0, abs_tol=abs_tol_zero):
        # Purely imaginary
        imag_coeff_val = abs(c.imag)
        imag_coeff_str = ""
        # Check if coefficient of #j is 1 or -1
        if not cmath.isclose(imag_coeff_val, 1.0, rel_tol=1e-9, abs_tol=abs_tol_zero):
            imag_coeff_str = f"{imag_coeff_val:.{precision}g}".rstrip('0').rstrip('.')

        imag_unit_str = "#j"
        full_imag_str = f"{imag_coeff_str}{imag_unit_str}"
        return full_imag_str if c.imag > 0 else f"-{full_imag_str}"

    # Mixed real and imaginary
    real_part_str = f"{c.real:.{precision}g}".rstrip('0').rstrip('.')
    imag_coeff_val = abs(c.imag)
    imag_coeff_str = ""
    if not cmath.isclose(imag_coeff_val, 1.0, rel_tol=1e-9, abs_tol=abs_tol_zero):
        imag_coeff_str = f"{imag_coeff_val:.{precision}g}".rstrip('0').rstrip('.')

    imag_unit_str = "#j"
    imag_part_combined = f"{imag_coeff_str}{imag_unit_str}"

    # Determine sign for the imaginary part
    imag_sign = "+" if c.imag > 0 else "-"
    if c.imag < 0 and imag_coeff_str.startswith('-'): # if imag_coeff_str was already like "-2"
        imag_part_combined = f"{imag_coeff_str[1:]}{imag_unit_str}" # use abs value essentially
        imag_sign = "-"
    elif c.imag > 0 and imag_coeff_str.startswith('-'): # Should not happen if abs() is used correctly
         imag_part_combined = f"{imag_coeff_str[1:]}{imag_unit_str}"
         imag_sign = "-"


    return f"({real_part_str}{imag_sign}{imag_part_combined})"


def _format_number_as_aop(num: Union[Decimal, complex, float, int], base: int, get_letter: Callable, precision: int, allow_squash: bool = True, is_coeff_formatting: bool = False) -> str:
    if isinstance(num, complex) and not cmath.isclose(num.imag, 0, abs_tol=1e-14): # Handle actual complex numbers first
        return _complex_to_str(num, precision)

    num_decimal: Decimal
    if isinstance(num, complex): # Real complex number, e.g. complex(3.0, 0.0)
        num_decimal = Decimal(str(num.real))
    else: # float, int, or Decimal
        num_decimal = Decimal(str(num)) # Ensure it's a Decimal; str() preserves precision for float->Decimal

    # Normalize integer Decimals (e.g., Decimal('3.0') -> Decimal('3'))
    if num_decimal == num_decimal.to_integral_value(rounding=decimal.ROUND_HALF_UP):
        # Check if the number has a fractional part by examining the exponent
        exponent = num_decimal.as_tuple().exponent
        if isinstance(exponent, int) and exponent < 0:
            num_decimal = num_decimal.quantize(Decimal('1'), rounding=decimal.ROUND_HALF_UP)

    if not num_decimal.is_finite(): return str(num_decimal) # Handles 'Infinity', 'NaN'
    if num_decimal.is_zero(): return "0" # The number 0 itself always formats to "0"
    if num_decimal == Decimal(1) and not is_coeff_formatting and allow_squash : return "1" # Standalone number 1 is "1"

    # Priority 1: Direct Letter for VALUE (e.g., if num_decimal is 100 (base 10), it should become 'b')
    # This rule applies if the number itself IS the value represented by an AoP letter.
    if not is_coeff_formatting: # Only for standalone values
        # Check if num_decimal is a value represented by an AoP letter (e.g., 100 (base 10) is 'b')
        # This must come AFTER the True/False check for 1/0 if we want 1/0 to be True/False.
        # If a letter happens to be base^1 or base^0, this could conflict.
        # Let's assume letters are for exponents > 1 for this specific rule.
        # Ensure it's not 1 (already handled) and is a positive integer.
        if num_decimal > Decimal(1) and \
           num_decimal == num_decimal.to_integral_value(rounding=decimal.ROUND_HALF_UP):
            try: # Check if num_decimal is base^L_exp
                log_val = num_decimal.ln() / Decimal(base).ln()
                if abs(log_val - log_val.to_integral_value(rounding=decimal.ROUND_HALF_UP)) < Decimal("1e-50"):
                    exponent_represented = int(log_val.to_integral_value(rounding=decimal.ROUND_HALF_UP))
                    if exponent_represented in EXPONENT_TO_LETTER_MAP: # Check if this exponent has a letter
                        return EXPONENT_TO_LETTER_MAP[exponent_represented] # e.g., value 100 -> 'b'
            except Exception: pass

    # Priority 1.5 (Squash for Coefficients to a^ExpNumStr form) has been removed.
    # The enhanced Priority 2 (Coeff-Letter^Power) is generally preferred for coefficients.

    # Priority 2: Coefficient-Letter representation with power notation (e.g., 2000 -> 2c, or 2YYYY -> 2Y^4)
    if num_decimal == num_decimal.to_integral_value(rounding=decimal.ROUND_HALF_UP):
        num_int_val = num_decimal.to_integral_value(rounding=decimal.ROUND_HALF_UP) # Get it as an integer type for modulo

        original_num_int_val = num_int_val # Keep original for iterating letters

        for L_exp_val in sorted(EXPONENT_TO_LETTER_MAP.keys(), reverse=True): # Iterate letter exponents
            if L_exp_val <= 0: continue
            current_letter_char = get_letter(L_exp_val)
            current_letter_base_val = Decimal(base) ** L_exp_val

            if current_letter_base_val.is_zero() or current_letter_base_val == Decimal('1'): continue # Avoid dividing by zero or one indefinitely
            if original_num_int_val % current_letter_base_val != 0: # Check against original number
                continue

            # Count how many times this letter_value divides num_int_val
            power_of_letter = 0
            # Use a temporary variable for division to find the prime coefficient
            coeff_tracker = original_num_int_val
            while coeff_tracker % current_letter_base_val == 0:
                power_of_letter += 1
                coeff_tracker /= current_letter_base_val

            # After loop, coeff_tracker is the prime coefficient.
            # power_of_letter is how many times current_letter_char was a factor.
            if power_of_letter > 0:
                formatted_prime_coeff = _format_number_as_aop(coeff_tracker, base, get_letter, precision, allow_squash=False, is_coeff_formatting=True)

                # The power_of_letter is a literal count here.
                power_str = str(power_of_letter)

                # Assemble: Coeff + Letter + ^Power (if power > 1)
                result_str = ""
                if formatted_prime_coeff != "1" or power_of_letter == 0: # Show "1" if it's just "1" (no letter part)
                    result_str += formatted_prime_coeff
                elif formatted_prime_coeff == "-1": # Handle -1 coefficient for -L^P form
                    result_str += "-"

                result_str += current_letter_char

                if power_of_letter > 1:
                    result_str += f"^{power_str}" # Parentheses around power_str not needed for simple int

                # Heuristic: Only use this form if it's strictly shorter than the plain number string,
                # or if we are formatting a coefficient (where AoP structure is preferred).
                plain_number_str = str(original_num_int_val)
                if is_coeff_formatting or len(result_str) < len(plain_number_str):
                    return result_str
                # Else, this Coeff-Letter^Power form is not better, continue loop for other letters
                # or fall through to P3/P4 if no other letter yields a shorter P2 form.
        # Fall through if no suitable Coeff-Letter^Power found by this enhanced P2
        # The original P2 logic (simple coeff*letter) is now superseded by this more general one.
        # If the loop completes without returning, it means num_int_val was not formattable by this P2.

    # Priority 3: "Squashing" into a^... form for perfect powers of the base.
    # Only attempt squashing if not formatting a coefficient (P1.5 handles coeff squashing).
    if allow_squash and not is_coeff_formatting and num_decimal > 0 and num_decimal.is_finite():
        try:
            exponent_val_for_squash = num_decimal.ln() / Decimal(base).ln()
            if abs(exponent_val_for_squash - exponent_val_for_squash.to_integral_value(rounding=decimal.ROUND_HALF_UP)) < Decimal("1e-50"):
                exp_int = exponent_val_for_squash.to_integral_value(rounding=decimal.ROUND_HALF_UP)
                # Recursively format the new exponent, allowing it to be squashed further or become coeff-letter.
                exp_str = _format_number_as_aop(exp_int, base, get_letter, precision, allow_squash=True, is_coeff_formatting=False)
                return f"a^({exp_str})" if any(c in exp_str for c in ' *()+^-') else f"a^{exp_str}"
        except Exception: pass

    # Priority 4: Fallback to plain string representation
    if isinstance(num_decimal, Decimal) and num_decimal.is_finite():
        # For finite Decimals, use their direct string representation.
        # str(Decimal) usually provides full precision without forcing E-notation unless necessary
        # for very extreme exponents outside typical fixed-point representation.
        s = str(num_decimal)
        # If Decimal was an integer but str() added ".0" (e.g. from quantize or some operations)
        if num_decimal.as_tuple().exponent == 0 and s.endswith(".0"): # Check if it's an integer ending in .0
            s = s[:-2]
        return s
    return _complex_to_str(complex(num_decimal), precision) # For initial complex, or non-finite Decimals


def format_term(term: AoPTerm, base: int, get_letter: Callable, precision: int) -> str:
    prefer_symbolic = False
    if not isinstance(term.exponent, AoPValue):
        try:
            # Use Decimal directly if term.exponent is already one, otherwise convert carefully
            exp_val_for_check = term.exponent if isinstance(term.exponent, Decimal) else Decimal(str(complex(term.exponent).real))
            if exp_val_for_check.is_finite():
                exp_mag = abs(exp_val_for_check)
                if exp_mag > 250: # Heuristic threshold
                    prefer_symbolic = True
        except Exception:
            prefer_symbolic = True

    try:
        if prefer_symbolic: raise PracticalLimitError("Exponent too large or complex, prefer symbolic term formatting")
        numerical_value_of_term = term.to_numerical(base)
        return _format_number_as_aop(numerical_value_of_term, base, get_letter, precision, allow_squash=True, is_coeff_formatting=False)
    except PracticalLimitError:
        coeff_str = _complex_to_str(term.coeff, precision)
        exp_str = ""

        # Handle exponent formatting for the symbolic path
        if isinstance(term.exponent, AoPValue):
            exp_str = format_output(term.exponent, base, get_letter, OutputFormatMode.AOP, precision)
            if len(term.exponent.terms) > 1 or any(c in exp_str for c in ' *()+^-'):
                exp_str = f"({exp_str})"
        else: # term.exponent is a simple number (Decimal, complex, int, float)
            # Determine if the exponent part itself can be squashed (e.g. a^10000 -> a^(a^d))
            # This applies if the term's coefficient is 1.
            can_squash_exponent = cmath.isclose(term.coeff, 1.0) and cmath.isclose(term.coeff.imag,0)
            exp_str = _format_number_as_aop(term.exponent, base, get_letter, precision, allow_squash=can_squash_exponent, is_coeff_formatting=False)

        # Assemble the symbolic term string
        if cmath.isclose(term.coeff, 1.0) and cmath.isclose(term.coeff.imag,0):
             # If exponent was 0 and formatted to "0", result is "a^0" (which is 1, handled by numeric path ideally)
             # If _format_number_as_aop returned "1" for exponent 0, this becomes "a^1", wrong.
             # This path is for non-zero exponents or symbolic ones.
            return f"a^{exp_str}"
        if cmath.isclose(term.coeff, -1.0) and cmath.isclose(term.coeff.imag,0):
            return f"-a^{exp_str}"

        # If exponent was numerically 0 (and formatted to "0" string)
        is_exp_zero = False
        if not isinstance(term.exponent, AoPValue):
            try:
                if cmath.isclose(complex(term.exponent), 0, abs_tol=1e-14):
                    is_exp_zero = True
            except TypeError: pass # Not a number

        if is_exp_zero and exp_str == "0": # Check formatted string too
             return coeff_str # e.g. for a complex coefficient like (1+2#j) * base^0

        display_coeff_str = coeff_str
        # If base is 10, coefficient is "10", and we are multiplying an "a^..." part, prefer "a" for the coefficient.
        if base == 10 and coeff_str == "10" and exp_str: # Ensure exp_str is not empty
            display_coeff_str = "a"
        return f"{display_coeff_str}*a^{exp_str}"

def format_output(value: AoPValue, base: int, get_letter: Callable, mode: OutputFormatMode, precision: int) -> str:
    if not value.terms: return "0"

    # Auto mode tries to simplify single term results further
    if mode == OutputFormatMode.AUTO and len(value.terms) == 1:
        term = value.terms[0]
        # Try to format as a single numerical value first using the term formatter's numeric path
        try:
            # This re-evaluates the term numerically and formats it.
            # This path ensures things like Term(1,100) -> a^b
            # or Term(2,3) -> 2c
            single_term_str = format_term(term, base, get_letter, precision)

            # Additional auto-mode check: if the result is a direct letter for an exponent
            # and the coefficient was 1 (e.g. Term(1,3) -> c, not a^c)
            if cmath.isclose(term.coeff, 1.0) and cmath.isclose(term.coeff.imag, 0) and \
               not isinstance(term.exponent, AoPValue):
                try:
                    exp_val_direct = complex(term.exponent)
                    if cmath.isclose(exp_val_direct.imag, 0):
                        exp_int_direct = int(round(exp_val_direct.real))
                        if cmath.isclose(exp_val_direct.real, exp_int_direct, rel_tol=1e-9, abs_tol=1e-14) and 1 <= exp_int_direct <= 50 :
                            if letter_direct := get_letter(exp_int_direct):
                                return letter_direct # e.g. 10^3 -> c
                except Exception:
                    pass # Fall through if not a simple integer exponent
            return single_term_str # Use the result from format_term
        except Exception: # Fallback if format_term itself had an issue (should not happen)
            pass # Continue to general list formatting

    if mode in (OutputFormatMode.SCIENTIFIC, OutputFormatMode.NUMERICAL):
        try:
            num = value.to_numerical(base)
            if not cmath.isfinite(num): # Handle cases where to_numerical might return inf/nan
                return str(num)
            if mode == OutputFormatMode.SCIENTIFIC:
                return f"{num.real:.{precision}e}" if cmath.isclose(num.imag, 0, abs_tol=1e-14) else _complex_to_str(num, precision)
            else: # NUMERICAL mode
                return _complex_to_str(num, precision)
        except (OverflowError, PracticalLimitError, NotImplementedError) as e:
            # If full numerical evaluation fails, try to format symbolically in AOP mode as fallback
            # This prevents "Error: ..." for sci/num mode if AOP form is possible
            # Logging is not defined, so skip logging for now
            # Fallthrough to AOP formatting code below
            pass
        # If fallthrough from SCIENTIFIC/NUMERICAL, ensure mode is AOP for symbolic parts
        mode = OutputFormatMode.AOP


    # Default to AOP mode formatting (list of terms)
    parts = [format_term(t, base, get_letter, precision) for t in value.terms]
    if not parts: return "0" # Should be caught by value.terms check, but for safety

    result = parts[0]
    for part_idx in range(1, len(parts)):
        part_str = parts[part_idx]
        # Determine if the part represents a negative value by its string form
        # This is a bit heuristic; ideally, we'd check the term's coefficient.
        # However, format_term already produces "-value" for negative terms.
        if part_str.startswith('-'):
            result += f" - {part_str[1:]}"
        else:
            result += f" + {part_str}"
    return result
