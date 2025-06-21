# aop_operations.py

This module implements core mathematical operations for the Alphabet of Powers system, handling both numerical and symbolic representations.

## Key Functions

### `simplify_value(val: AoPValue, base: int = 10) -> AoPValue`
Combines terms and optimizes representation through:
1. Recursive exponent simplification
2. Numerical summation when possible
3. Coefficient absorption into exponents
4. Term grouping by exponent

```python
# Example: Simplify 2*10^3 + 3*10^3 → 5*10^3
simplify_value(AoPValue([AoPTerm(2,3), AoPTerm(3,3)]))
# Returns AoPValue([AoPTerm(5,3)])
```

### `add_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue`
Performs term-wise addition:
```python
# (2*10^3) + (3*10^4) → AoPValue with two terms
```

### `multiply_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue`
Handles multiplication through:
1. Scalar optimization for simple values
2. Term-by-term symbolic multiplication
3. Exponent addition
```python
# (2*10^3) * (3*10^4) → 6*10^7
```

### `power_value(base_val: AoPValue, power_val: AoPValue, base: int) -> AoPValue`
Computes exponents using:
1. Numerical path for computable values
2. Symbolic path for massive numbers
3. Handles both simple and tower exponents
```python
# (10^3)^2 → 10^6
```

### `equals_values(v1: AoPValue, v2: AoPValue, base: int = 10) -> AoPValue`
Compares values numerically with tolerance:
- Returns AoPValue(1) if equal within tolerance
- Returns AoPValue(0) otherwise
```python
# 10^100 == Z → 1
```

### Division and Subtraction
- `divide_values`: Implements multiplication by inverse
- `subtract_values`: Uses term negation

## Algorithmic Approach
1. **Numerical First**: Attempts high-precision Decimal calculations
2. **Symbolic Fallback**: Uses AoPValue representation when numbers are too large
3. **Logarithmic Handling**: For symbolic powers (base^(P * (log_base(C) + E)))

## Error Handling
- `PracticalLimitError`: Raised when numbers exceed computational limits
- Falls back to symbolic representation on overflow
