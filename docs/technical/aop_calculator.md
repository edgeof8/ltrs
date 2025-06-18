# aop_calculator.py

Implements the core calculator logic and REPL environment.

## Key Classes

### `AoPCalculator`

Main calculator class with state management.

#### Key Methods

- `__init__(self, base=10)`: Initialize with base
- `evaluate_expression(self, expr: str)`: Parse and evaluate expression
- `set_base(self, new_base)`: Change numerical base
- `set_mode(self, mode_name)`: Set output formatting mode

### `AoPState`

Manages calculator state including:

- Current base
- Variables
- Output mode
- Precision

## REPL Implementation

Handles special commands:

```python
def handle_command(self, command: str):
    if command.startswith('/setbase '):
        # Parse and set new base
    elif command == '/vars':
        # Show defined variables
    elif command.startswith('/graph'):
        # Plot expression
```

## Evaluation Workflow

1. Parse expression to AST
2. Recursively evaluate nodes
3. Apply AoP operations
4. Format result based on current mode

## Configuration

- `OutputMode`: Enum (AUTO, AOP, SCI, NUM)
- `PowerAssociativity`: (LEFT, RIGHT)

## Example Usage

```python
from aopl_python_impl.aop_calculator import AoPCalculator

calc = AoPCalculator(base=10)
result = calc.evaluate_expression("j^j^j")
print(result)  # a^a^u
