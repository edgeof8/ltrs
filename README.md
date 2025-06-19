# The Alphabet of Powers (AoP) Calculator

Welcome to the Alphabet of Powers (AoP) Calculator, a unique command-line tool that explores a novel system of representing and manipulating numbers of all scales, from the everyday to the truly astronomical. This calculator is not just a tool; it's an exploration into number theory, symbolic algebra, and the limits of computation.

## The Core Concept

In the AoP system (with the default base 10), letters represent powers of the base:

- **Lowercase `a-y`**: `a` = `10^1`, `b` = `10^2`, ..., `y` = `10^25`.
- **Uppercase `A-Y`**: `A` = `10^26`, `B` = `10^27`, ..., `Y` = `10^50`.

Words are multiplicative, with their power being the sum of their letters' exponents:

- `cab` => `c*a*b` => `10^3 * 10^1 * 10^2` => `10^(3+1+2)` => `10^6`, which simplifies to **`f`**.
- `aA` => `a*A` => `10^1 * 10^26` => `10^27`, which simplifies to **`B`**.

This simple, powerful idea allows for a new way of understanding and manipulating numbers, especially at the hyper-power scale.

## Features

- **Symbolic & Numerical Engine**: The calculator uses a **Numeric-First, Symbolic-Fallback** engine. It attempts to compute all expressions as numbers, providing concrete answers when possible.
- **Hyper-power Ready**: When a calculation would overflow standard numerical types (e.g., `3^3^3^3`), the engine gracefully falls back to a symbolic representation, allowing for the manipulation of numbers far beyond the limits of conventional calculators.
- **Letter-First Formatting**: Results are always displayed in their most elegant and compact form. A result of `10^40` is not shown as a raw number, but as its canonical letter, **`O`**.
- **Arbitrary Base**: Explore the AoP system in any integer base using the `--base` flag. Discover new mathematical relationships, such as `2d = e` in base 2 (`2 * 2^4 = 2^5`).
- **Full Operator Support**: Supports `+`, `-`, `*`, `/`, and `^` (power), with correct order of operations and right-associativity for powers.
- **Implicit Multiplication**: Understands natural algebraic syntax like `2b` (2 *b) and `a(b+c)` (a* (b+c)).
- **Built-in Constants**: Recognizes `#pi`, `#e`, `#phi` (the golden ratio), `#tau` (2π), `#sqrt2`, and `#j` (the imaginary unit).

## Installation

1. Clone the repository:

    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2. (Optional) Create a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install dependencies (if any):

    ```bash
    # Currently no external dependencies required for the core calculator
    ```

4. (Optional) Create a simple alias or script named `ltrs` for easy access:
    - **Linux/macOS** (in your `.bashrc` or `.zshrc`):

        ```bash
        alias ltrs='python -m aopl_python_impl.aop_calculator_cli'
        ```

    - **Windows** (using a `ltrs.bat` file in your PATH):

        ```batch
        @echo off
        python -m aopl_python_impl.aop_calculator_cli %*
        ```

## Usage

The calculator is run from the command line.

### Basic Syntax

```bash
ltrs "expression" [options]
```

### Examples

#### Simple Operations

- **`c^2`** (c squared)

    ```bash
    $ ltrs "c^2"
    f
    ```

    *Explanation: `c` is `10^3`. `(10^3)^2` is `10^6`, which is `f`.*

- **`e/b`** (e divided by b)

    ```bash
    $ ltrs "e/b"
    c
    ```

    *Explanation: `10^5 / 10^2` is `10^3`, which is `c`.*

#### Symbolic Powers

- **`d^a`** (d to the power of a)

    ```bash
    $ ltrs "d^a"
    O
    ```

    *Explanation: The engine evaluates this numerically. `d` is `10^4`, `a` is `10`. The result is `(10^4)^10 = 10^40`, which is `O`.*

- **`b^c`** (b to the power of c)

    ```bash
    $ ltrs "b^c"
    a^2c
    ```

    *Explanation: `(10^2)^(10^3)` is `10^2000`. The formatter elegantly represents `2000` as `2*1000`, which is `2c`.*

#### Hyper-powers and Symbolic Fallback

- **`j^j`** (j to the power of j)

    ```bash
    $ ltrs "j^j"
    a^k
    ```

    *Explanation: `(10^10)^(10^10)` is `10^(10 * 10^10) = 10^(10^11)`. The exponent is `10^11`, which is `k`. The result is `a^k`.*

- **The Graham's Number Precursor**

    ```bash
    $ ltrs "3^3^3^3"
    a^3638334640024
    ```

    *Explanation: `3^(3^27)` is too large for any standard number type. The engine correctly overflows and switches to a symbolic representation, calculating the final exponent `log10(3) * 3^27` and displaying it as a power of `a`.*

#### Different Bases

- **Coefficient Absorption in Base 2**

    ```bash
    $ ltrs --base 2 "2d"
    e
    ```

    *Explanation: In base 2, `2` is `2^1` or `a`. `d` is `2^4`. The expression is `a * d = 2^1 * 2^4 = 2^5`, which is `e`.*

- **Symbolic Powers in Base 2**

    ```bash
    $ ltrs --base 2 "b^c"
    p
    ```

    *Explanation: In base 2, `b` is `2^2`, `c` is `2^3=8`. The expression is `(2^2)^8 = 2^16`, which is `p`.*

### Command-Line Options

| Flag          | Alias | Description                                        | Default |
|---------------|-------|----------------------------------------------------|---------|
| `--base`      | `-b`  | The numerical base for calculations.               | `10`    |
| `--mode`      | `-m`  | Output format: `auto`, `aop`, `sci`, `num`.        | `auto`  |
| `--precision` | `-p`  | Decimal precision for numerical output.            | `10`    |
| `--debug`     | `-d`  | Enable debug logging to `aop_calculator_debug.log`.| `False` |
|---------------|-------|----------------------------------------------------|---------|
