# Usage Guide

This guide explains how to use the `ltrs` command-line interface (CLI) and interactive REPL environment.

## Command-Line Interface (CLI)

Evaluate expressions directly from your terminal:

```bash
ltrs "expression" [options]
```

### Basic Evaluation

```bash
ltrs "cat"               # → x (10^24)
ltrs "a * b"             # → c (10^3)
ltrs "dog^2 / z"         # → z
ltrs "sin(#pi/2) + log(a)" # → 2
ltrs "#phi^2 - #phi - 1" # → 0 (golden ratio identity)
```

### CLI Options

| Option | Description | Example |
|--------|-------------|---------|
| `--mode <mode>` | Output formatting: `auto`, `aop`, `sci`, `num` | `ltrs "12345" --mode aop` → `1.2345 * d` |
| `--base <num>` | Set numerical base (≥2) | `ltrs "a+b" --base 2` → `6` |
| `--precision <digits>` | Set decimal precision | `ltrs "#pi" --precision 5` → `3.14159` |
| `--debug` | Enable debug output | `ltrs "j^j^j" --debug` |
| `-h`, `--help` | Show help message | `ltrs --help` |

### Special Commands

- **`history [n]`**: Show last n commands (default 10)

  ```bash
  ltrs history
  ltrs history 5
  ```

- **`explain [expr]`**: Get AI explanation

  ```bash
  ltrs explain "j^j^j"
  ltrs explain "sin(#pi)"
  ```

## Interactive REPL Environment

Launch with `ltrs`:

```bash
ltrs
```

### REPL Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show available commands | |
| `/exit` | Exit REPL | |
| `/history [n]` | Show command history | `/history 5` |
| `/explain [expr]` | AI explanation | `/explain j^j^j` |
| `/vars` | Show defined variables | |
| `/setbase <num>` | Change numerical base | `/setbase 2` |
| `/setmode <mode>` | Set output mode | `/setmode sci` |
| `/setprecision <digits>` | Set decimal precision | `/setprecision 15` |
| `/graph <expr>` | Plot expression | `/graph x^2 for x from -5 to 5` |
| `/savevars <file>` | Save variables to file | `/savevars session1` |
| `/loadvars <file>` | Load variables from file | `/loadvars session1` |

## Graphing Expressions

Visualize functions using matplotlib:

```bash
# Plot parabola
/graph x^2 for x from -5 to 5

# Logarithmic scale
/graph b^x for x from 0 to 3 --logy

# Trigonometric function
/graph sin(t) for t from 0 to #pi * 2

# With variable
my_offset = a
/graph x^2 + my_offset for x from -10 to 10
```

## Expression Syntax

### Terms and Constants

| Type | Examples | Description |
|------|----------|-------------|
| Letters | `a`, `z` | `a` = `base^1`, `z` = `base^26` |
| Words | `cat`, `dog` | Multiplicative: `cat` = `c*a*t` |
| Coefficients | `2b`, `-0.5x` | `2b` = `2 * b` |
| Numbers | `10`, `1.23e4` | Standard and scientific notation |
| Constants | `#pi`, `#e`, `#phi` | Mathematical constants |

### Operators

| Operator | Description | Precedence |
|----------|-------------|------------|
| `^` | Exponentiation | Highest |
| `*` | Multiplication | |
| `/` | Division | |
| `+` | Addition | |
| `-` | Subtraction | Lowest |

### Functions

| Function | Description | Example |
|----------|-------------|---------|
| `sqrt(expr)` | Square root | `sqrt(d)` → `b` |
| `log(expr)` | Base-10 log | `log(c)` → `3` |
| `ln(expr)` | Natural log | `ln(#e)` → `1` |
| `log2(expr)` | Base-2 log | `log2(16a)` → `7.32` |
| `sin(expr)` | Sine (radians) | `sin(#pi/2)` → `1` |
| `cos(expr)` | Cosine | `cos(0)` → `1` |
| `tan(expr)` | Tangent | `tan(#pi/4)` → `1` |
| `asin(expr)` | Arcsine | `asin(1)` → `#pi/2` |
| `acos(expr)` | Arccosine | `acos(0)` → `#pi/2` |
| `atan(expr)` | Arctangent | `atan(1)` → `#pi/4` |
| `sinh(expr)` | Hyperbolic sine | `sinh(0)` → `0` |
| `cosh(expr)` | Hyperbolic cosine | `cosh(0)` → `1` |
| `tanh(expr)` | Hyperbolic tangent | `tanh(0)` → `0` |

### Variables

Assign and use values:

```bash
radius = 2.5b      # 2.5 * 10^2 = 250
area = #pi * radius^2
/vars
```

### Parentheses

Control order of operations:

```bash
(a + b) * c   # Different from a + b * c
```

For more examples, see the [[Examples]] page.
