# aop_formatter.py

Handles formatting AoP values for display in different output modes.

## Key Classes

### `AoPFormatter`

Main class for formatting AoP values based on configuration.

#### Key Methods

- `format_value(value: AoPValue)`: Format based on current mode
- `_format_auto(value)`: Smart default formatting
- `_format_aop(value)`: Prioritize AoP letter representation
- `_format_scientific(value)`: Use scientific notation
- `_format_numerical(value)`: Display as plain number

## Output Modes

1. **Auto (default)**:
   - Tries nice numerical representation
   - Falls back to AoP letters or scientific
2. **AoP**:
   - Uses coefficient-letter form (e.g., `1.23 * b`)
   - Applies normalization
3. **Scientific**:
   - Always `X * base^Y` format
4. **Numerical**:
   - Plain numbers when possible
   - Scientific for large/small values

## Formatting Process

1. Simplify value
2. Check for special cases (zero, unity)
3. Apply mode-specific formatting:
   - Handle complex numbers
   - Format coefficients and exponents
   - Recursive formatting for nested values

## Example Usage

```python
from aopl_python_impl.aop_formatter import AoPFormatter
from aopl_python_impl.aop_value import AoPValue, AoPTerm

formatter = AoPFormatter(base=10, mode='aop')
value = AoPValue([AoPTerm(1.0, 3)])  # 10^3
print(formatter.format_value(value))  # 'c'
