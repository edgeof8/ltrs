# definitions.py

Defines constants, enums, and shared data structures for the AoP Calculator.

## Key Components

### Enums

- `OutputMode`: AUTO, AOP, SCI, NUM
- `PowerAssociativity`: LEFT, RIGHT
- `CommandType`: REPL command categories

### Constants

- `LETTER_EXPONENTS`: Mapping of letters to exponents
- `LETTER_EXPONENTS_UPPER`: Uppercase letters mapping
- `SPECIAL_CONSTANTS`: #pi, #e, #phi, etc.
- `FUNCTIONS`: sqrt, log, sin, etc.

### Data Structures

- `ValueTuple`: (coefficient, exponent) representation
- `AlphaZone`: For very large exponents
- `Unity`: Represents the value 1

### Configuration

- `DEFAULT_BASE`: 10
- `DEFAULT_PRECISION`: 10
- `DEFAULT_ASSOCIATIVITY`: RIGHT

## Example Usage

```python
from aopl_python_impl.definitions import OutputMode, LETTER_EXPONENTS

mode = OutputMode.AOP
letter_value = LETTER_EXPONENTS['c']  # 3
