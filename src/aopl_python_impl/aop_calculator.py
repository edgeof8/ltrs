# aopl_python_impl/aop_calculator.py
import re
import logging
from .definitions import OutputFormatMode, OPERATORS, TOKEN_REGEX, AoPError, LETTER_TO_EXPONENT_MAP, EXPONENT_TO_LETTER_MAP
from .aop_value import AoPValue, AoPTerm
from .aop_parser import tokenize_expression, infix_to_rpn, evaluate_rpn
from .aop_operations import simplify_value
from .aop_term_handler import get_term_value
# --- THIS IS THE FIX ---
# Import the new master formatter function
from .aop_formatter import format_output
# --- END OF FIX ---

class AoP_Calculator:
    def __init__(self, base: int = 10, load_default_vars: bool = True):
        """Initializes the calculator with a specific base."""
        self.base = base
        self.letter_to_exponent = LETTER_TO_EXPONENT_MAP
        self.exponent_to_letter = EXPONENT_TO_LETTER_MAP
        self.token_regex = TOKEN_REGEX
        self.variables: dict[str, AoPValue] = {}
        self.operators_map = OPERATORS.copy() # type: ignore
        if load_default_vars:
            self._load_default_variables()

    def format_aop_value(self, value: AoPValue, mode: OutputFormatMode, precision: int) -> str:
        """
        Formats a given AoPValue object into a string representation.
        """
        # The AoPValue from variables should already be simplified.
        # If not, or for safety: simplified_value = simplify_value(value, self.base)
        def get_letter_func(exp: int) -> str:
            return self.exponent_to_letter.get(exp, "")
        return format_output(value, self.base, get_letter_func, mode, precision)

    def _load_default_variables(self):
        """
        Loads a set of predefined variables.
        Numerical constants are stored as their value (coeff with exp 0).
        AoP structural constants (like $googol=Z) are defined in terms of the current calculator base.
        """
        from decimal import Decimal  # Local import for clarity

        # Helper to create an AoPValue from a numerical literal
        def num_val(number_str: str) -> AoPValue:
            return AoPValue.from_number(Decimal(number_str))

        # Helper to create an AoPValue for base^exponent (where exponent is a direct number)
        def aop_direct_power(exp_val: int) -> AoPValue:
            return AoPValue([AoPTerm(1, Decimal(str(exp_val)))])

        # Numerical Constants (their value is fixed, their AoP string representation depends on base)
        self.variables['$one'] = num_val("1")
        self.variables['$thousand'] = num_val("1E3")  # More descriptive than $kilo if value is fixed
        self.variables['$million'] = num_val("1E6")
        self.variables['$billion'] = num_val("1E9")
        self.variables['$trillion'] = num_val("1E12")
        # You can continue SI prefixes if desired: $quadrillion (1E15), $quintillion (1E18), etc.
        # For these, using their AoP letter if base=10 is also an option, e.g. $kilo = self.evaluate_expression("c",...)
        # but num_val makes their *value* base-independent.

        # AoP Structural Constants (value depends on the calculator's current base)
        # These use the AoP letters defined for the current base.
        if 'Z' in LETTER_TO_EXPONENT_MAP:
            z_exp = LETTER_TO_EXPONENT_MAP['Z']  # This is 100
            # $googol represents current_base^100
            self.variables['$googol'] = aop_direct_power(z_exp)  # e.g., Z if formatted

            # $googolplex represents current_base^(current_base^100)
            # Exponent of 'a' (base^1) is the AoPValue representing Z_value (current_base^100)
            val_Z_as_exponent = aop_direct_power(z_exp)  # This is an AoPValue for current_base^100
            self.variables['$googolplex'] = AoPValue([AoPTerm(1, val_Z_as_exponent)])  # a^(Z_value)
        else:  # Fallback if Z is not defined (e.g. user modified definitions.py)
            self.variables['$googol'] = num_val("1E100")  # Fallback to numerical 10^100
            # Googolplex would be too complex to define robustly without 'a^Z' structure

        # Famous Large Numbers - these are complex and often base-10 centric in their common definition
        # For G1 = 3^3^3^3, its AoP form a^X is base-10 specific for X's value.
        # Storing them as strings to be evaluated by the GUI on demand might be more flexible,
        # or only define them if self.base == 10.
        if self.base == 10:
            # G1_exp_val = Decimal("3.6383346400240996866889081313645E12")  # Approx exp for a^(...)
            # self.variables['$GrahamG1_AoP'] = AoPValue([AoPTerm(1, G1_exp_val)])
            self.variables['$GrahamG0'] = num_val("7625597484987")  # 3^3^3, a finite number
            # $GrahamG1 would be 3^($GrahamG0), which is huge.
            # For now, let's not precalculate G1's a^X form to keep this simpler.
            # Users can define $G1 = 3^$GrahamG0 or $G1 = 3^3^3^3 in the GUI.

        logging.debug(f"Loaded default variables: {list(self.variables.keys())}")

    def set_power_associativity(self, mode: str):
        if mode.lower() in ('right', 'left'):
            self.operators_map['^']['associativity'] = mode.lower()
            self.operators_map['**']['associativity'] = mode.lower()
        else: raise ValueError("Invalid associativity mode. Use 'left' or 'right'.")

    def evaluate_expression(self, expression: str, mode: OutputFormatMode, precision: int) -> str:
        """
        Evaluates an expression and formats it according to the given mode and precision.
        """
        logging.debug(f"--- Starting Evaluation ---")
        logging.debug(f"Expression: '{expression}', Base: {self.base}, Mode: {mode.value}")
        try:
            tokens = tokenize_expression(expression, self.token_regex)
            rpn = infix_to_rpn(tokens, self.operators_map)
            result = evaluate_rpn(rpn, self.variables, get_term_value, self.base)
            logging.debug(f"Raw evaluation result: {result!r}")
            simplified_result = simplify_value(result, self.base)

            def get_letter_func(exp: int) -> str:
                return self.exponent_to_letter.get(exp, "")

            # --- THIS IS THE FIX ---
            # Call the new master formatter function instead of the old method
            logging.debug(f"Simplified result for formatting: {simplified_result!r}")
            return format_output(simplified_result, self.base, get_letter_func, mode, precision)
            # --- END OF FIX ---

        except (AoPError, ZeroDivisionError, OverflowError, ValueError, NotImplementedError) as e:
            logging.error(f"Evaluation error: {type(e).__name__}: {e}", exc_info=True)
            # Return a clean error string
            return f"Error: {e}"
