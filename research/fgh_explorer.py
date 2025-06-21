# research/fgh_explorer.py
import sys
import os

# Ensure the aopl_python_impl package can be found
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.definitions import OutputFormatMode

def generate_fgh_expression(alpha, n):
    """
    Generates an AoP expression string for f_alpha(n) in the Fast-Growing Hierarchy.
    """
    if alpha == 0:
        return f"{n+1}"
    if alpha == 1:
        return f"{2*n}"
    if alpha == 2:
        # f_2(n) is a power tower of n's of height n.
        return '^'.join([str(n)] * n)
    if alpha == 3:
        # f_3(n) applies f_2 n times. f_3(2) = f_2(f_2(2))
        if n == 2:
            # f_2(2) = 2^2 = 4
            # f_2(f_2(2)) = f_2(4) = 4^4^4^4
            return generate_fgh_expression(2, 4)
        # A proper recursive implementation for n > 2 is needed next.
        return f"f_3({n})_placeholder"

    return f"f_{alpha}({n})_unsupported"

def main():
    """
    Main function to run the FGH exploration.
    """
    # We use base 2 as it was identified as the most promising.
    calculator = AoP_Calculator(base=2, load_default_vars=False)
    results = []

    print("--- FGH Exploration for f_3(3) ---")
    results.append("--- FGH Exploration for f_3(3) ---")

    # Script to calculate f_3(3) = f_2(f_2(f_2(3)))
    # The calculator maintains state, so variables are preserved.
    script = [
        "# Step 1: Calculate the innermost value, f_2(3) = 3^3^3",
        "$val1 = 3^3^3",

        "# Step 2: Calculate f_2(f_2(3)) = f_2($val1).",
        "# This would be a tower of $val1 of height $val1. This is impossible to express.",
        "# Let's test the largest expressible component: the base raised to itself.",
        "$result = $val1 ^ $val1"
    ]

    for expression in script:
        if expression.startswith('#'):
            results.append(expression)
            continue

        calc_result = calculator.evaluate_expression(expression, OutputFormatMode.AOP, 15)
        results.append(f"Input: {expression} | Result: {calc_result}")

    # --- Write results to file ---
    output_path = "research/fgh_results.txt"
    with open(output_path, 'w') as outfile:
        outfile.write("\n".join(results))

    print(f"FGH script evaluation complete. Results written to {output_path}")

if __name__ == "__main__":
    main()
