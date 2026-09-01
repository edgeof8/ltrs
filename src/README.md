# Alphabet of Powers (AoP) Engine

This directory contains the core symbolic algebra engine for the **Cosmic Scratchpad** project. It is a standalone Python library designed for arbitrary-precision arithmetic using a novel symbolic representation called the "Alphabet of Powers."

While the main graphical interface is the primary way to interact with the system, this engine can be used directly as a command-line tool or imported as a library into other Python projects.

## Core Design Philosophy

The engine's power comes from a single, fundamental concept: **numbers are not stored as single, massive integers.** Instead, every value is represented by an `AoPValue` object, which is essentially a **sparse polynomial**.

For example, in base 10, the number `1024` is not stored as `1024`. It is stored as the abstract idea:

`1 * base^3 + 2 * base^1 + 4 * base^0`

This is represented internally as a dictionary-like structure: `{@3:1, @1:2, @0:4}`. The same polynomial is written as the AoP literal **`c2a4`** (or `c + 2a + 4`): **adjacent letters add**. Multiplication is always explicit (`a*b` → `c`), never implied by concatenating letters (`ba` is `b+a`, not `b*a`).

All mathematical operations (`+`, `-`, `*`, `/`, `^`) are performed on these polynomial objects in the Rust core (`aop_rust_core`). This approach allows the engine to handle numbers of astronomical size with ease, as it only needs to manipulate the coefficients and exponents of the polynomial, which are themselves small numbers. The final, gigantic number is only ever assembled at the very end, during the formatting stage.

**Division** is exact. The engine first tries sparse schoolbook division in \(\mathbb{Z}[X]\) (where \(X\) is the calculator base), so monomials cancel (`c / a` → `b`) and polynomials that divide evenly stay symbolic (`(a + b) / a` → `a + 1`). If that formal division fails because `_simplify` has already carried a value — `10` is stored as \(X^1\), so `10 / 2` is `X / 2` in \(\mathbb{Z}[X]\) — it falls back to exact integer division and re-encodes the quotient (`5`). Inexact quotients (`11 / 2`, `a / b`) and divide-by-zero raise `AoPError`; the engine never truncates.

## The Calculation Pipeline

Every expression goes through a three-stage pipeline:

1. **Parsing (`aop_parser.py`):** The input string (e.g., `"5b^2d"`) is converted into a structured Abstract Syntax Tree (AST). The parser is robust and handles:
    * Standard operator precedence.
    * Right-associativity for powers (`^`).
    * **Additive letter juxtaposition:** a multi-letter AoP literal such as `ba` or `cab` is one polynomial (`b+a`, `c+a+b`), not a product.
    * A coefficient on a single letter (`2d`) is a scaled monomial (`2 * d`). Parentheses still imply multiplication (`a(b+c)`).
    * Parentheses for grouping.

2. **Evaluation (`aop_operations.py`):** The engine recursively walks the AST. Each node is evaluated to produce an `AoPValue` object. This is where the core mathematical logic resides.
    * `Number('5')` becomes `AoP({@2:1, @0:1})` in base 2.
    * `Identifier('d')` becomes `AoP({@4:1})`.
    * These `AoPValue` objects are then added, multiplied, divided, or raised to a power through `aop_value.py`, which dispatches to Rust.

3. **Formatting (`aop_formatter.py`):** The final `AoPValue` object is converted into a human-readable string. This can be:
    * **Numerical (`num` mode):** The polynomial is fully calculated into its decimal string representation.
    * **Symbolic (`aop` mode):** unit monomials use the letter map (`a*b` → `c`, `a^b` → `Z`). Other polynomials print as sums of letters.

## Project Structure (`/src/aopl_python_impl/`)

* `aop_calculator.py`: The main controller class. It orchestrates the pipeline from string input to string output.
* `aop_value.py`: Python handle for the Rust `AoPValue`. Forwards `__add__`, `__sub__`, `__mul__`, `__truediv__`, and `__pow__` to the compiled extension.
* `aop_rust_core/`: Rust crate that implements sparse polynomial add/sub/mul, exact division (`divide_poly`), and power.
* `aop_parser.py`: The tokenizer and Pratt parser that builds the AST. `/` has the same precedence as `*` and is left-associative.
* `aop_operations.py`: The evaluation logic that traverses the AST and calls `AoPValue` methods (including `/`).
* `aop_formatter.py`: Formats a final `AoPValue` into a user-friendly string (`num` or `aop`).
* `aop_logger.py`: Debug calculation reports (`--debug`).
* `aop_calculator_cli.py`: The entry point for the command-line interface (`ltrs`).
* `definitions.py`: Token, error, and symbolic-power types.

## Usage as a Library

The engine is designed to be easily imported and used by other applications, such as the Cosmic Scratchpad GUI.

```python
from aopl_python_impl.aop_calculator import AoP_Calculator

# Initialize the calculator for a specific base
calc = AoP_Calculator(base=2)

# Evaluate an expression
expression = "5b^2d"
result = calc.evaluate_expression(expression, mode="aop")

print(f"The result of '{expression}' in base 2 is: {result}")
# Output: The result of '5b^2d' in base 2 is: a^(g + c + a) + ...
```

From a checkout, install the package so the library and `ltrs` script are available:

```bash
pip install -e .
ltrs "a*b" --mode aop
python -m aopl_python_impl.aop_calculator_cli "5b^2d" --base 2 --mode aop --debug
```

`pip install -e ".[gui]"` also installs Cosmic Scratchpad dependencies and the `cosmic-scratchpad` command.

## The Calculation Report (`--debug` mode)

The engine features a powerful debug mode that generates a beautiful, self-documenting report on the entire calculation process. This is the best way to understand the internal workings of the engine.

It provides a full trace from parsing to evaluation to final formatting, complete with a symbol glossary.

**Example Command:**

```bash
python -m aopl_python_impl.aop_calculator_cli "5b^2d" --base 2 --mode aop --debug
```
