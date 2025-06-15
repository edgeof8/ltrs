# Usage Guide

This guide explains how to use the `ltrs` command-line interface (CLI).

## Command-Line Interface (CLI)

Once [[Installation|installed]], you can use `ltrs` directly from your terminal to evaluate Alphabet of Powers (AoP) expressions and access other features.

### 1. Evaluating Expressions

You can pass an AoP expression directly to the `ltrs` command. If your expression contains spaces or special shell characters, enclose it in quotes.

**Basic Syntax:**

```bash
ltrs "<expression>"
```

**Examples (assuming default base 10 and auto mode):**

```bash
ltrs "cat"               # Output: x
ltrs "2a * 5b"           # Output: d
ltrs "dog^2 / z"         # Output: z
ltrs "sin(#pi/2) + log(a)" # Output: 2
ltrs "#phi^2 - #phi - 1" # Output: 0 (approximately, due to float precision)
ltrs "1.23e7"             # Output: 1.23 * 10^7
ltrs "cat+dog"            # Output: 1.01 * 10^26
```

### 2. CLI Options

You can modify the behavior of the calculator using command-line options:

- `--mode <mode>`: Sets the output formatting style.
  - `auto` (default): Smart default, tries to show numbers nicely, then AoP letters, then normalized AoP.
  - `aop`: Prioritizes AoP letter or coefficient-letter form (e.g., `1.23 * b`). Uses normalization.
  - `sci` (or `scientific`): Always uses scientific notation in the format `X * 10^Y` (e.g., `1.23 * 10^2`).
  - `num` (or `numerical`): Tries to show as a plain number, falls back to scientific if too large/small.
- `--base <number>`: Sets the calculator's numerical base for AoP calculations (e.g., `a = base^1`). Default is 10. Must be an integer >= 2.
- `--precision <number>`: Sets the numerical precision for displaying floating-point numbers. Default is 10.
- `--debug`: Enables debug mode for more verbose error output, including tracebacks for unexpected errors.
- `-h` or `--help`: Displays the help message with all available options.

**Examples with Options:**

```bash
ltrs "12345" --mode aop
# Output: 1.2345 * d

ltrs "12345" --mode scientific --precision 3
# Output: 1.23 * 10^4

ltrs "a+b" --base 2 --mode numerical
# Output: 6  (since a=2^1=2, b=2^2=4, a+b=6)
```

### 3. CLI Commands

Besides direct expression evaluation, `ltrs` supports a few built-in commands:

- **`history [limit]`**: Displays the history of recently evaluated successful expressions and their results.

  - `limit` (optional): A positive integer specifying the maximum number of history items to show. Defaults to 10.
  - Example: `ltrs history`
  - Example: `ltrs history 5`

- **`explain [expression]`**: Explains the last successfully evaluated expression or the given `[expression]` using an AI service.
  - If `[expression]` is omitted, it explains the most recent item from the history.
  - Requires the `OPENROUTER_API_KEY` environment variable to be set (see README.md).
  - Example (explain last): `ltrs "a*b"` then `ltrs explain`
  - Example (explain specific): `ltrs explain "sqrt(-1) + c"`

### 4. Variable Assignment

You can assign the result of an expression to a variable using the `=` operator within an expression string.

```bash
ltrs "my_var = a * b"
# Output: c (result of a*b)
```

**Note:** In the current direct CLI mode, variables are not persisted between separate `ltrs` command invocations. Each call to `ltrs` uses a new calculator instance. Variable assignment is primarily useful when using the `AoP_Calculator` class programmatically within a Python script.

## Expression Syntax

The AoP expression syntax supports a variety of terms, constants, operators, and functions:

- **Terms:**
  - Single letters: `a`, `z` (representing `base^1` to `base^26`).
  - Words: `cat` (multiplicative, e.g., `c*a*t`).
  - Coefficients: `2b` (meaning `2 * b`), `-0.5x`.
  - Numbers: `10`, `1.23`, `1.23e4` (parsed as `1.23 * 10^4`), complex numbers like `(3+4j)`.
  - `Unity(1)`: Represents the numerical value 1.
- **Constants:**
  - `#pi` or `π` (Pi, ~3.14159)
  - `#e` (Euler's number, ~2.71828)
  - `#phi` or `φ` (Golden Ratio, ~1.61803)
  - `#tau` or `τ` (Tau, 2\*Pi, ~6.28318)
  - `#sqrt2` (Square root of 2, ~1.41421)
  - `#j` (Imaginary unit, same as `(0+1j)`)
- **Operators (standard precedence applies):**
  - `+` (addition)
  - `-` (subtraction, unary minus)
  - `*` (multiplication)
  - `/` (division)
  - `^` (power)
- **Functions (trigonometric functions expect arguments in radians):**
  - `sqrt(expr)`: Square root.
  - `log(expr)`: Base-10 logarithm.
  - `ln(expr)`: Natural logarithm.
  - `log2(expr)`: Base-2 logarithm.
  - `sin(expr)`, `cos(expr)`, `tan(expr)`
  - `asin(expr)`, `acos(expr)`, `atan(expr)`
  - `sinh(expr)`, `cosh(expr)`, `tanh(expr)`
- **Parentheses:** `()` for grouping expressions to control order of operations.

For more details on the underlying system and library features, refer to the main [README.md](../README.md).
