# aop_value.py

Defines the core data structures for representing AoP values.

## Key Classes

### `AoPTerm`

Represents a single term in AoP notation: `coefficient * (base^exponent)`

#### Properties

- `coeff`: Coefficient (complex number)
- `exponent`: Exponent (numeric or AoPValue for recursive representation)

### `AoPValue`

Represents a value as a collection of AoPTerms.

#### Key Methods

- `from_number(n)`: Create from numeric value
- `to_numerical(base)`: Convert to numerical value
- `simplify()`: Combine like terms
- `__str__()`: Format for display

## Special Values

- `Unity(1)`: Represents 1
- `AlphaZone`: For massive exponents
- `ZERO`: Represents 0

## Recursive Representation

Handles massive numbers through nested exponents:

```python
# Representation of j^j (10^10^10)
term = AoPTerm(1.0, AoPValue([AoPTerm(10.0, 0)]))
value = AoPValue([term])
```

## Type Handling

- Supports complex coefficients
- Decimal for precise calculations
- Automatic conversion between types

## Example Usage

```python
from aopl_python_impl.aop_value import AoPValue, AoPTerm

# Create 10^3 (c)
term = AoPTerm(1.0, 3)
value = AoPValue([term])

# Create complex number
complex_term = AoPTerm(3+4j, 0)
complex_value = AoPValue([complex_term])
