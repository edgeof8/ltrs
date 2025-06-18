# aop_calculator_cli.py

Implements the command-line interface for the AoP Calculator.

## Key Components

### `main()`

Entry point for CLI execution.

### Argument Parsing

Uses `argparse` to handle:

- Expression input
- Mode selection (`--mode`)
- Base configuration (`--base`)
- Precision setting (`--precision`)
- Debug mode (`--debug`)
- Special commands (`history`, `explain`)

### Command Handling

- `handle_history(args)`: Show command history
- `handle_explain(args)`: Generate AI explanation
- `evaluate_expression(expr, args)`: Evaluate AoP expression

### Output Handling

- Formats results based on selected mode
- Handles errors and debug output
- Colorizes output when supported

## REPL Implementation

- Uses `cmd.Cmd` for interactive shell
- Implements command completion
- Handles special REPL commands:
  - `/setbase`, `/setmode`, `/setprecision`
  - `/vars`, `/history`, `/explain`
  - `/graph`, `/savevars`, `/loadvars`

## Example Usage

```python
# Direct expression evaluation
ltrs "cat" --mode aop

# Start REPL
ltrs

# Explain expression
ltrs explain "j^j^j"
```

## Error Handling

- Catches and displays evaluation errors
- Handles invalid commands gracefully
- Provides suggestions for correct usage
