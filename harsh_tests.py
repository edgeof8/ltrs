import subprocess
import sys

import subprocess
import sys
from typing import Optional

def run_test(expression: str, expected_output: Optional[str] = None):
    print(f"Testing: '{expression}'")
    command = [sys.executable, "-m", "aopl_python_impl.aop_calculator_cli", expression]
    process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

    output = process.stdout.strip()
    error_output = process.stderr.strip()

    if process.returncode != 0:
        print(f"  FAIL (CLI Error): {error_output}")
    elif expected_output is not None and output != expected_output:
        print(f"  FAIL (Mismatch)")
        print(f"    Expected: '{expected_output}'")
        print(f"    Got:      '{output}'")
    else:
        print(f"  PASS")
        print(f"    Result: '{output}'")
    print("-" * 30)

print("Running Harsh Test Suite for AoP Calculator\n")

# Test Cases
# 1. Deeply nested power towers (symbolic)
run_test("a^b^c^d^e", "a^(a^(a^(a^(a^5))))") # Assuming a=10^1, b=10^2, c=10^3, d=10^4, e=10^5
run_test("j^j^j^j", "a^(10a^(10a^k))") # From previous perfect test case

# 2. Power towers with numeric bases/exponents, testing factorization
run_test("b^c", "a^2000") # Should be a^2000, not (2000)
run_test("b^2c", "a^4000") # Should be a^4000, not (4000)
run_test("a^2000", "a^(2c)") # Test factorization directly

# 3. Mixed symbolic and numeric operations
run_test("a^4dy", "a^(4dY)") # Should factorize 4dY if possible, or just 4dY
run_test("2*a^b", "2a^b") # Implicit multiplication
run_test("100*a", "c") # Coefficient simplification

# 4. Edge cases for coefficients and exponents
run_test("1/0", "Division by zero.")
run_test("a+b", "110") # Numeric addition
run_test("c^a", "E") # Numeric power to letter

# 5. Large numbers and formatting
run_test("10000000000000000000000000Y", "1e25Y") # Large coefficient with letter

# 6. Complex numbers (if supported and relevant)
# run_test("(1+j)*a", "(1+j)a") # Example complex multiplication

# 7. Negative exponents
run_test("a^-1", "a^-1")
run_test("1/a", "a^-1")

# 8. Zero exponents
run_test("a^0", "1")
run_test("5^0", "1")

# 9. Complex nested expressions
run_test("(a+b)^2", "12100") # (110)^2 = 12100
run_test("a^(b+c)", "a^(b+c)") # Symbolic exponent addition

print("\nHarsh Test Suite Complete.")
