# The Alphabet of Powers (AoP) Calculator

A unique symbolic and numerical calculation system where letters correspond to powers of a configurable base (default is 10), enabling powerful algebraic manipulations.

## Overview

This project implements "The Alphabet of Powers" (AoP), a system where each letter of the alphabet represents a power of a base number. For example, in base 10:

- `a = 10^1 = 10`
- `b = 10^2 = 100`
- `c = 10^3 = 1,000`
- ...
- `y = 10^25 = 10 septillion`

This allows for compact representation and manipulation of very large numbers through word-like structures, with applications in mathematics education, cryptography, and algorithm design.

## Features

- **Symbolic Calculation**: Work with letters as powers (e.g., `cat = c * a * t = 10^3 * 10^1 * 10^20 = 10^24`).
- **Numerical Calculation**: Seamless integration with standard numbers and operations.
- **Configurable Base**: Change the base to any number greater than 1 (default is 10).
- **AI-Powered Explanations**: Get natural language explanations of complex calculations.
- **CPU Simulation**: Explore different multiplication algorithms (schoolbook, Karatsuba, AoP-specific).
- **Power Associativity Setting**: Configure whether exponentiation is evaluated as left-associative (e.g., `(a^b)^c`) or right-associative (e.g., `a^(b^c)`), with right-associative as the default to match standard mathematical convention.

## Installation

```bash
pip install ltrs
```

## Usage

### Interactive REPL

Launch the interactive calculator with:

```bash
ltrs
```

#### REPL Commands

- `/help`: Shows a list of available commands.
- `/exit`: Exits the interactive session.
- `/history [limit]`: Displays recent successful calculations.
- `/explain [expr]`: Explains the last calculation or a new one using AI.
- `/vars`: Shows all currently defined variables.
- `/setbase <num>`: Changes the calculator's base.
- `/setmode <mode>`: Sets the output mode (`auto`, `aop`, `sci`, `num`).
- `/setprecision <num>`: Sets the floating-point output precision.
- `/setassoc <mode>`: Sets power associativity (`left` or `right`). Default is `right` (e.g., `a^b^c` is `a^(b^c)`).

### Single-Shot Commands

You can also evaluate a single expression directly.

**Syntax:** `ltrs "[expression]" [options]`

**Examples:**

- Evaluate a simple expression:

  ```bash
  ltrs "2a * 5b"
  # Output: d
  ```

- Use a different base and associativity:

  ```bash
  # Standard (right-associative) power - default
  ltrs "j^j^j"
  # Output: a^a^k

  # Left-associative power
  ltrs "j^j^j" --assoc left
  # Output: u
  ```

## Project Structure

- `src/aopl_python_impl/`: Core implementation of the AoP system.
  - `aop_core.py`: Fundamental operations and data structures.
  - `aop_calculator.py`: Main calculator logic.
  - `aop_parser.py`: Expression parsing.
  - `aop_formatter.py`: Output formatting.
  - `aop_operations.py`: Mathematical operations.
  - `aop_term_handler.py`: Handling of terms and variables.
  - `aop_ai_explainer.py`: AI-based explanation generation.
  - `aop_visualizer.py`: Visualization utilities.
  - `aop_calculator_cli.py`: Command-line interface.
  - `cpu_sim/`: CPU simulation for algorithm performance.
- `tests/`: Unit tests for all components.
- `docs/`: Documentation files.

## Development

To contribute or modify the project:

1. Clone the repository.
2. Install dependencies: `pip install -e .`
3. Run tests: `pytest tests/`

## License

MIT

## Contact

For questions or contributions, please open an issue or pull request on the GitHub repository.
