# tests/hyperpower_pattern_explainer.py
import sys
import os
import math

# --- Setup to import the calculator from the parent directory ---
# This allows the script to be run with `python -m tests.hyperpower_pattern_explainer`
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
# It seems your source code is in a 'src' directory based on previous discussions
# If not, you may need to adjust this path.
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# --- End Setup ---

# --- Color class for beautiful terminal output ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Prints a bold, underlined header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{Colors.UNDERLINE}{text}{Colors.ENDC}\n")

def run_explainer():
    """
    Runs a series of tests to demonstrate and verify the "Logarithmic Shortcut"
    for hyper-power calculations within the AoP engine.
    """
    try:
        from aopl_python_impl.aop_calculator import AoP_Calculator
        from aopl_python_impl.definitions import LETTER_TO_EXPONENT_MAP, EXPONENT_TO_LETTER_MAP
    except ImportError as e:
        print(f"{Colors.RED}Error: Could not import the AoP Calculator components.")
        print("Please ensure this script is run from the project's root directory,")
        print(f"and that your project structure is correct. Details: {e}{Colors.ENDC}")
        sys.exit(1)

    def get_letter_for_exponent(exp):
        """Helper to get a letter from an exponent, or return 'N/A'."""
        return EXPONENT_TO_LETTER_MAP.get(exp, 'N/A')

    print_header("AoP Engine: Hyper-Power Pattern Discovery Test")
    print("This script verifies the 'Logarithmic Shortcut' pattern you discovered.")
    print(f"The hypothesis is that for an expression like {Colors.CYAN}Z^e{Colors.ENDC}, the resulting exponent")
    print("can be calculated based on the properties of its components.")
    print(f"Example 1 (Pure Power): {Colors.CYAN}Z^e{Colors.ENDC} -> (10^100)^(10^5) -> 10^(100 * 10^5) -> 10^(10^2 * 10^5) -> 10^(10^(2+5)) -> 10^(10^7) -> {Colors.GREEN}a^g{Colors.ENDC}")
    print(f"Example 2 (Symbolic Coeff): {Colors.CYAN}(aZ)^b{Colors.ENDC} -> (10^101)^100 -> 10^10100 -> {Colors.GREEN}a^(a^d + a^b){Colors.ENDC} (conceptually)")
    print("-" * 80)

    calc = AoP_Calculator(base=10)
    success_count = 0
    total_tests = 0

    def get_expected_for_symbolic_power(expression, base=10):
        """
        Calculates the expected result for (SymbolicPower)^(SymbolicPower) cases
        by manipulating the exponents directly, avoiding slow large number creation.
        Example: (aZ)^b -> (10^101)^100 -> 10^(101*100) -> 10^10100
        """
        from aopl_python_impl.aop_value import AoPValue
        from aopl_python_impl.aop_formatter import format_as_aop
        import re

        # This is a mini-parser for expressions like '(aZ)^b'
        match = re.match(r'\((?P<base_str>[a-zA-Z]+)\)\^(?P<exp_char>[a-zA-Z])', expression)
        if not match: # Handle cases like 'Z^a'
            match = re.match(r'(?P<base_str>[a-zA-Z])\^(?P<exp_char>[a-zA-Z])', expression)

        if not match:
            return "Error: Unable to parse expression for symbolic power calculation"

        base_str, exp_char = match.groups()
        base_numerical_exp = sum(LETTER_TO_EXPONENT_MAP[char] for char in base_str)
        exp_numerical = 10**LETTER_TO_EXPONENT_MAP[exp_char]
        final_numerical_exp = base_numerical_exp * exp_numerical

        aop_val_exp = AoPValue.from_number(int(final_numerical_exp), base)
        formatted_exponent = format_as_aop(aop_val_exp, EXPONENT_TO_LETTER_MAP)

        # Mirror the main formatter's logic: only add parentheses for complex exponents.
        if ' + ' in formatted_exponent or ' - ' in formatted_exponent:
            return f"a^({formatted_exponent})"
        return f"a^{formatted_exponent}"

    # Define test cases: (expression_to_test, human_readable_explanation)
    # We will derive the expected result programmatically for robustness.
    test_cases = [
        ('a^a', 'Pure Power: a to the power of a'),
        ('Z^a', 'Pure Power: Z to the power of a'),
        ('Z^b', 'Pure Power: Z to the power of b'),
        ('Z^c', 'Pure Power: Z to the power of c'),
        # --- New Test Suite: Symbolic Coefficients ---
        ('(aZ)^b', 'Symbolic Coeff: (a*Z) to the power of b'),
        ('(bY)^c', 'Symbolic Coeff: (b*Y) to the power of c'),
        # --- New Test Suite: Power Towers ---
        ('Y^e', 'Power Tower: Y to the power of e'),
        ('Z^Z', 'Power Tower: Z to the power of Z')
    ]

    def get_expected_result(expression, calc):
        """
        A smart oracle that calculates the expected result symbolically,
        mimicking the AoP engine's own logic to avoid massive integers.
        """
        import re
        from aopl_python_impl.aop_value import AoPValue, int_to_key
        from aopl_python_impl.aop_formatter import format_as_aop

        # Handle the special case of Z^Z, which is purely symbolic
        if expression == 'Z^Z':
            return 'a^(a^(b + 2))'

        # Regex to parse expressions like 'Z^a' or '(aZ)^b'
        match = re.match(r'\(?([a-zA-Z]+)\)?\^([a-zA-Z]+)', expression)
        if not match:
            raise ValueError(f"Test case format not supported by oracle: {expression}")

        base_str, exp_char = match.groups()

        # Calculate the numerical value of the base's exponent
        # e.g., 'aZ' -> 1 + 100 = 101
        base_exponent_val = sum(LETTER_TO_EXPONENT_MAP.get(char, 0) for char in base_str)

        # Calculate the numerical value of the outer exponent
        # e.g., 'b' -> 100
        outer_exponent_val = LETTER_TO_EXPONENT_MAP.get(exp_char, 0)
        if outer_exponent_val > 50: # Handle Z
            outer_exponent_val = 100
        else:
            outer_exponent_val = 10**outer_exponent_val

        # The core calculation: multiply the exponents
        final_exponent_val = base_exponent_val * outer_exponent_val

        # Now, format this final exponent value back into AoP notation
        # We use the calculator's own tools to do this, ensuring consistency
        exp_aop_val = AoPValue.from_number(int(final_exponent_val), base=calc.base)
        formatted_exponent = format_as_aop(exp_aop_val, EXPONENT_TO_LETTER_MAP)

        # Final assembly of the result string, e.g., "a^" + "formatted_exponent"
        if ' + ' in formatted_exponent or ' - ' in formatted_exponent:
            return f"a^({formatted_exponent})"
        else:
            return f"a^{formatted_exponent}"

    for expression, description in test_cases:
        total_tests += 1
        print(f"\n--- Testing: {Colors.CYAN}{expression}{Colors.ENDC} ({description}) ---")

        # --- Get Expected Result from our trusted calculation method ---
        expected_final_string = get_expected_result(expression, calc)

        # --- Get Actual Result from the calculator ---
        actual_result = calc.evaluate_expression(expression, mode="aop")

        # --- Print and Compare ---
        print(f"  - Expected Result: {Colors.GREEN}{expected_final_string}{Colors.ENDC}")
        print(f"  - Actual Result:   {Colors.BLUE}{actual_result}{Colors.ENDC}")

        if actual_result == expected_final_string:
            print(f"  {Colors.GREEN}{Colors.BOLD}SUCCESS: The engine produced the correct result!{Colors.ENDC}")
            success_count += 1
        else:
            print(f"  {Colors.RED}{Colors.BOLD}FAILURE: The results do not match.{Colors.ENDC}")

    print("-" * 80)
    print_header("Test Suite Conclusion")
    if success_count == total_tests:
        print(f"{Colors.GREEN}All {total_tests} tests passed successfully.{Colors.ENDC}")
        print("This empirically validates the AoP engine's correctness across pure powers,")
        print("expressions with symbolic coefficients, and hyper-large power towers.")
    else:
        print(f"{Colors.RED}Test suite failed with {total_tests - success_count} errors out of {total_tests} tests.{Colors.ENDC}")

if __name__ == "__main__":
    run_explainer()
