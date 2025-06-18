# interfaces.py

Defines abstract base classes for the AoP Calculator system using Python's ABC module.

## Key Interfaces

### `IAoPValue`

Interface for AoP value representation.

#### Methods

- `simplify()`: Combine like terms
- `to_numerical(base)`: Convert to numerical value
- `__str__()`: String representation
- `__add__(other)`: Addition
- `__sub__(other)`: Subtraction
- `__mul__(other)`: Multiplication
- `__truediv__(other)`: Division
- `__pow__(other)`: Exponentiation

### `IAoPTerm`

Interface for individual terms in AoP values.

#### Properties

- `coeff`: Coefficient
- `exponent`: Exponent (numeric or IAoPValue)

### `IAoPCalculator`

Interface for calculator implementations.

#### Methods

- `evaluate_expression(expr)`: Parse and evaluate
- `set_base(new_base)`: Change numerical base
- `set_mode(mode_name)`: Set output format
- `handle_command(command)`: Process REPL commands

## Implementation Notes

- Concrete classes implement these interfaces
- Ensures consistent API across components
- Enables modular design and testing

## Example Usage

```python
from aopl_python_impl.interfaces import IAoPValue

class CustomValue(IAoPValue):
    def simplify(self):
        # Custom implementation
        pass
