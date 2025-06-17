# The Alphabet of Powers (AoP) Calculator

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)[![Status](https://img.shields.io/badge/

**The Alphabet of Powers (AoP) Calculator is not just another calculator. It's a tool for thinking about numbers on an astronomical scale.**

Standard calculators fail around `10^308`. This calculator begins where they end. It can compute, represent, and simplify numbers so vast they cannot be written down in our universe. It does this by treating numbers not as single values, but as symbolic structures based on a simple, intuitive "alphabet" of exponents.

## The Core Concept

In the AoP system (with the default base 10), letters represent powers of the base:

- **Lowercase `a-y`**: `a` = `10^1`, `b` = `10^2`, ..., `y` = `10^25`.
- **Uppercase `A-Y`**: `A` = `10^26`, `B` = `10^27`, ..., `Y` = `10^50`.

Words are multiplicative:

- `cab` means `c * a * b` -> `10^3 * 10^1 * 10^2` -> `10^(3+1+2) = 10^6`, which is `f`.
- `aA` means `a * A` -> `10^1 * 10^26` -> `10^27`, which is `B`.

This simple, powerful idea allows for a new way of understanding and manipulating numbers.

## Features That Set It Apart

### 1. Hyper-Operation Engine

This calculator was built to handle operations that would cause an immediate overflow error on any standard tool. It excels at tetration (repeated exponentiation), which is evaluated **right-associatively** to match mathematical convention.

- **Standard Calculator:** `10^10^100` -> `Error`
- **AoP Calculator:** `a^j^b` -> `a^(j^b)` -> `a^(a^k)`

The AoP Calculator doesn't just store the expression; it *calculates* the result and simplifies it into a canonical AoP form.

### 2. Recursive Symbolic Representation

The true power lies in its internal engine. An AoP number is stored as a recursive structure: `Value = Coeff * (Base ^ Exponent)`, where the `Exponent` can be another `Value`. This allows for logarithmic memory compression.

- The number representing `j^j^j^j` would require more atoms than exist in the universe to write down.
- The AoP Calculator represents it elegantly as `a^a^a^a^31`, storing it in a tiny, nested data structure.

### 3. Intuitive Language for Scale

The AoP system transforms the incomprehensible scales of large numbers into a tangible, alphabetic system. The difference between `10^26` and `10^27` is hard to grasp, but the step from `A` to `B` is intuitive. This makes it an exceptionally powerful educational tool.

## Full Feature List

- **Symbolic Calculation**: Work with letters as powers (`cat = x`, `aA = B`).
- **Hyper-Power Engine**: Natively handles tetration and other hyper-operations.
- **Recursive Internal Representation**: Can represent numbers far beyond the limits of standard data types.
- **Configurable Base**: Change the base to any number greater than 1 (default is 10).
- **Power Associativity Setting**: Configure `^` to be left- or right-associative (default: `right`).
- **Interactive REPL**: A powerful read-eval-print loop with history, variable assignment, and special commands.
- **AI-Powered Explanations**: Get natural language explanations of complex calculations via OpenRouter.
- **CPU Simulation**: A sub-module to explore the performance of different large-number multiplication algorithms.

## Installation

To get started, clone the repository and install the dependencies.

```bash
git clone https://github.com/your-username/letter-powers.git
cd letter-powers
# It is recommended to use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

## Usage

The primary interface is the command-line tool `ltrs`.

### Basic Operations

```bash
# Multiplication
ltrs "c*a*t"
> x

# Division
ltrs "x/a"
> w

# Addition (converts to numerical form)
ltrs "a+b"
> 110
```

### Powers and Hyper-Powers

This is where the calculator shines. Remember, `^` is right-associative by default.

```bash
# Simple powers
ltrs "2j^2"
> 4t

# Tetration (a^b^c is evaluated as a^(b^c))
ltrs "j^j"
> a^k

ltrs "j^j^j"
> a^a^u

# An unimaginably large number, calculated and simplified instantly.
ltrs "j^j^j^j"
> a^a^a^31
```

### Interactive REPL

Launch the interactive calculator with `ltrs`.

**REPL Commands:** `/help`, `/exit`, `/history`, `/explain`, `/vars`, `/setbase <num>`, `/setmode <mode>`, `/setprecision <num>`, `/setassoc <mode>`.

## Project Structure

- `src/aopl_python_impl/`: Core implementation of the AoP system.
- `tests/`: Unit and integration tests.
- `docs/`: Additional documentation.

## Development

To contribute or modify the project:

1. Clone the repository.
2. Install in editable mode: `pip install -e .`
3. Run tests: `pytest`

## License

MIT

## Contact

For questions or contributions, please open an issue or pull request on the GitHub repository.
