# Coefficient Absorption Edge Cases (2025-06-20)

## Experiment 1: Basic Coefficient Absorption

**Command**: `python -m src.aopl_python_impl.aop_calculator_cli "2a * 5c" --base 10`
**Output**: `e` (10^5)

**Analysis**:
The expression 2a * 5c = 2*10^1 * 5*10^3 = 10*10^4 = 10^5 = e. The system correctly absorbs coefficients when they multiply to the base (2*5=10), demonstrating proper coefficient absorption in multiplication.

## Experiment 2: Coefficient Matching Base

**Command**: `python -m src.aopl_python_impl.aop_calculator_cli "10a" --base 10`
**Output**: `b` (10^2)

**Analysis**:
The expression 10a = 10*10^1 = 10^2 = b. This shows that when a coefficient equals the base (10 in base 10), it gets absorbed into the exponent, simplifying the expression according to AoP rules.

## Experiment 3: Non-absorbable Coefficients

**Command**: `python -m src.aopl_python_impl.aop_calculator_cli "11a" --base 10`
**Output**: `11a`

**Analysis**:
The expression 11a remains as 11a because 11 ≠ 10 (the base). This demonstrates that coefficients are only absorbed when they exactly match the base, preserving the coefficient otherwise.

**Key Insight**:
Coefficient absorption occurs exclusively when coefficients match the current base. This behavior maintains mathematical precision while optimizing notation when possible.
