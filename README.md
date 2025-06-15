# The Alphabet of Powers - Python Library and CLI Calculator (`ltrs`)

This project implements "The Alphabet of Powers" (AoP), a unique symbolic and numerical calculation system. Letters of the alphabet correspond to powers of a configurable base (default is 10), enabling powerful algebraic manipulation of large numbers.

The project provides a robust Python library for embedding AoP calculations into other applications and a feature-rich command-line interface (CLI) named `ltrs` for interactive and single-shot evaluations.

## Core Concepts

- **Letter-Exponent Mapping:** Letters 'a' through 'z' represent `base^1` through `base^26`. For the default `base=10`, `a` is 10, `b` is 100, and `j` is 10,000,000,000.
- **Word Multiplication:** Words are formed by multiplying their constituent letters. `cat` is `c * a * t`, which in base 10 is `10^3 * 10^1 * 10^20 = 10^24` (or `x`).
- **Symbolic Exponents:** The system can perform exponentiation symbolically. For example, `a^b` is `(10^1)^(10^2)`, which evaluates to `10^100`. This can be represented as `a^b`.
- **Complex Numbers:** Full support for complex numbers is included, using `#j` as the imaginary unit (e.g., `(3 + 4*#j)`).
- **Configurable Base:** The numerical base of the system can be changed at any time, allowing for calculations in different number systems (e.g., base 2, base 16).

## Features

- **Robust Expression Parsing:** A powerful parser based on the Shunting-yard algorithm handles complex expressions with correct operator precedence, parentheses, unary operators, and implicit multiplication (e.g., `2a` is treated as `2*a`).
- **Full Set of Mathematical Operations:**
  - Arithmetic: `+`, `-`, `*`, `/`, `^` (power).
  - Functions: A comprehensive suite of trigonometric (`sin`, `cos`), logarithmic (`log`, `ln`), and hyperbolic (`sinh`, `cosh`) functions.
  - Constants: `#pi` (π), `#e`, `#phi` (φ), `#tau` (τ), `#sqrt2`, and `#j` (imaginary unit).
- **Stateful Calculator:** The CLI and library support persistent variables within a session (e.g., `x = a * b`).
- **Configurable Output Formatting:**
  - **`auto` (Default):** Smartly formats results, showing simple numbers when possible (`2a` -> `20`) and falling back to AoP notation otherwise.
  - **`aop`:** Prioritizes the normalized AoP symbolic form (e.g., `123` -> `1.23 * b`).
  - **`scientific`:** Standard base-10 scientific notation (e.g., `1.23 * 10^2`).
  - **`numerical`:** Displays the full numerical result, falling back to scientific for very large/small numbers.
- **AI-Powered Explanations:** An `explain` command integrates with the OpenRouter AI API to provide natural language explanations of calculations, making it a powerful learning tool.
- **CPU Arithmetic Simulation:** The `cpu_sim` module provides a fascinating look into low-level integer arithmetic, with implementations and benchmarks for:
  - Schoolbook, Karatsuba, and a highly optimized AoP-specific multiplication algorithm.
  - Complex operations like integer power (`base ^ exponent`) and multiply-then-add.

## CLI Usage (`ltrs`)

The `ltrs` command-line tool is the primary interface for using the calculator.

### Installation

1.  **Prerequisites:** Python 3.9+
2.  **Installation:** Navigate to the project root directory and install the package:

    ```bash
    # For regular use
    pip install .

    # For development (recommended)
    pip install -e .
    ```

3.  **API Key (Optional):** To use the `/explain` command, you must get a free API key from [OpenRouter.ai](https://openrouter.ai/) and set it as an environment variable:

    ```bash
    # On Linux/macOS
    export OPENROUTER_API_KEY="your-key-here"

    # On Windows
    set OPENROUTER_API_KEY="your-key-here"
    ```

### Interactive Mode (REPL)

For an interactive session with persistent variables and history, simply run `ltrs` with no arguments.

```bash
ltrs
```

You will be greeted with a prompt:

```
Alphabet of Powers (AoP) Calculator - Interactive Mode
Type an expression, or a command like /history, /explain, /setbase <num>, /exit, /help.
aop> x = a*j
aop> x
k
aop> x / a
j
aop> /setbase 16
Base set to 16
aop> x = a*b
aop> x
c
aop> x + 0
4096
aop> /exit
Exiting AoP Calculator.
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

### Single-Shot Commands

You can also evaluate a single expression directly.

**Syntax:** `ltrs "[expression]" [options]`

**Examples:**

- Evaluate a simple expression:

  ```bash
  ltrs "2a * 5b"
  # Output: d
  ```

- Use a different base and output mode:

  ```bash
  ltrs "cat+dog" --base 10 --mode scientific --precision 3
  # Output: 1.01 * 10^26
  ```

- Explain a specific expression:
  ```bash
  ltrs explain "sqrt(-a^2)"
  ```

## Library Usage

You can easily incorporate the AoP calculator into your own Python projects.

```python
from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.definitions import OutputFormatMode

# Initialize the calculator
calc = AoP_Calculator(base=10, output_precision=8)

# Set output mode and evaluate
calc.output_format_mode = OutputFormatMode.AOP
result_aop = calc.evaluate_expression("12345")
print(f"AOP Mode: {result_aop}")
# Output: AOP Mode: 1.2345 * d

# Change mode
calc.output_format_mode = OutputFormatMode.SCIENTIFIC
result_sci = calc.evaluate_expression("12345")
print(f"Scientific Mode: {result_sci}")
# Output: Scientific Mode: 1.2345 * 10^4

# Use variables (state is preserved in the instance)
calc.evaluate_expression("my_var = c * 10") # my_var = 10^3 * 10 = 10^4
print(calc.evaluate_expression("my_var / a")) # (10^4) / (10^1) = 10^3
# Output (AOP mode): c
```

## Development and Testing

- **Source Code:** `src/aopl_python_impl/`
- **Tests:** `tests/`
- **Run Tests:** From the project root, run:
  ```bash
  python -m unittest discover -s tests
  ```
- **Run CPU Benchmarks:** To see the performance of the different multiplication algorithms, run the CPU simulation tests specifically:
  ```bash
  python -m unittest tests/test_raw_algorithms.py
  ```
