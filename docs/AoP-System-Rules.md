# Alphabet of Powers (AoP) System Rules

This document outlines the core rules and definitions of the Alphabet of Powers (AoP) mathematical system as implemented by the `ltrs` calculator.

## 1. Base System

- The AoP system operates on a numerical **base**, which is an integer greater than or equal to 2.
- The default base is 10.
- The base can be changed in the REPL using the `/setbase <number>` command. Changing the base clears all currently defined variables.

## 2. Letter-Exponent Mapping

- Each lowercase letter of the English alphabet ('a' through 'z') corresponds to an integer exponent.
- 'a' maps to exponent 1.
- 'b' maps to exponent 2.
- ...
- 'z' maps to exponent 26.
- The numerical value of a single letter `L` with exponent `exp_L` is `base^exp_L`.
  - Example (base 10): `a` = 10<sup>1</sup>, `b` = 10<sup>2</sup>.
  - Example (base 5): `a` = 5<sup>1</sup>, `c` = 5<sup>3</sup>.

## 3. Word Evaluation

- A "word" is a sequence of letters (e.g., "cat", "dog").
- The exponent of a word is the sum of the exponents of its constituent letters.
  - Example (any base): `cat` -> exponent_c + exponent_a + exponent_t = 3 + 1 + 20 = 24.
- The numerical value of a word is `base^word_exponent`.
  - Example (base 10): `cat` = 10<sup>24</sup>.
- Input words are case-insensitive (e.g., "Cat" is treated as "cat").

## 4. Internal Value Representation (`ValueTuple`)

- Internally, all AoP terms and results of AoP operations (like `*`, `/`, `^`) are represented as a tuple: `(coefficient: float, exponent: int)`.
- This tuple represents the value `coefficient * (base^exponent)`.
  - Example (base 10):
    - `a` -> `(1.0, 1)`
    - `c` -> `(1.0, 3)`
    - `2b` -> `(2.0, 2)` (representing 2 \* 10<sup>2</sup>)
    - `dog` (exponent 26) -> `(1.0, 26)`
- Numerical constants (like `123`, `#pi`) are represented as `(value, 0)`.

## 5. Operations

### 5.1. Multiplication (`*`)

- `(c1, e1) * (c2, e2)` results in `(c1 * c2, e1 + e2)`.
- This corresponds to: `(c1 * base^e1) * (c2 * base^e2) = (c1 * c2) * base^(e1 + e2)`.
- Example (base 10): `a * b` -> `(1.0, 1) * (1.0, 2)` -> `(1.0, 3)` (which is `c`).

### 5.2. Division (`/`)

- `(c1, e1) / (c2, e2)` results in `(c1 / c2, e1 - e2)`.
- This corresponds to: `(c1 * base^e1) / (c2 * base^e2) = (c1 / c2) * base^(e1 - e2)`.
- Example (base 10): `c / a` -> `(1.0, 3) / (1.0, 1)` -> `(1.0, 2)` (which is `b`).
- Division by a term evaluating to zero (coefficient is zero) results in an error.

### 5.3. Power (`^`)

- `(c, e) ^ n` (where `n` is a numerical value) results in `(c^n, e * n)`.
- The exponent `e * n` must result in an integer (or be very close to one).
- This corresponds to: `(c * base^e)^n = c^n * base^(e * n)`.
- Example (base 10): `a^3` -> `(1.0, 1)^3` -> `(1.0^3, 1*3)` -> `(1.0, 3)` (which is `c`).
- Example (base 10): `(2b)^2` -> `(2.0, 2)^2` -> `(2.0^2, 2*2)` -> `(4.0, 4)` (which is `4d`).

### 5.4. Addition (`+`) and Subtraction (`-`)

- These operations are performed **numerically**.
- Each AoP operand is first converted to its full numerical value: `coeff * (base^exponent)`.
- The addition or subtraction is then performed on these numerical values.
- The result is represented as a `ValueTuple`: `(numerical_sum_or_difference, 0)`.
- Example (base 10): `a + b` -> `10^1 + 10^2` -> `10 + 100` -> `110`. Result: `(110.0, 0)`.

## 6. Value Simplification (`simplify_value`)

- After an AoP operation (`*`, `/`, `^`), the resulting `(coefficient, exponent)` tuple is simplified if the `coefficient` is an exact power of the current `base`.
- If `coefficient = k * base^p` where `k` is +/-1.0 and `p` is an integer, the value is simplified to `(k, exponent + p)`.
  - Example (base 10): `(10.0, 3)` simplifies to `(1.0, 4)`. (e.g. `10c` becomes `d`)
  - Example (base 10): `(0.1, 2)` simplifies to `(1.0, 1)`. (e.g. `0.1b` becomes `a`)
- This simplification does **not** apply if the original `exponent` was 0 and the `coefficient` itself was a power of the base (e.g., `(10.0, 0)` remains `(10.0, 0)` and formats as "10", not "a").
- General normalization (like `20b` -> `2c`) is **not** performed by `simplify_value`.

## 7. Output Formatting

- The final `ValueTuple` is formatted for display.
- Preference is given to "nice" numerical representations if the value can be expressed as a simple integer or short float (e.g., `(110.0, 0)` -> "110", `(0.5, 2)` base 10 -> "50").
- If `coefficient` is 1.0 and `1 <= exponent <= 26`, the corresponding letter is shown (e.g., `(1.0, 1)` -> "a").
- Otherwise, forms like `coeff * letter`, `coeff * base^exponent`, or `AlphaZone` are used.

## 8. Special Values

- **`Unity(1)`**: Represents the value `(1.0, 0)`, i.e., `1 * base^0 = 1`.
- **`AlphaZone`**: Used for very large exponents (typically > 26 if `coefficient` is 1.0) where a simple letter representation is not available. The output shows the equivalent power in terms of simpler AoP terms if possible (e.g., `AlphaZone(10^b)` for 10<sup>100</sup>).

## 9. Functions

- **`sqrt(expr)`**: Calculates the square root. For an AoP term `(c,e)`, this is `(c^0.5, e/2)`. The term `e/2` must be an integer.
- **`log(expr)`, `ln(expr)`, `log2(expr)`**: Calculate base-10 log, natural log, and base-2 log, respectively. The `expr` is first evaluated to its full numerical value, then the logarithm is taken. The result is `(log_value, 0)`.
- **`sin(expr)`, `cos(expr)`, `tan(expr)`**: Calculate trigonometric functions. The `expr` is first evaluated to its full numerical value, which is assumed to be in **radians**. The result is `(trig_value, 0)`. `tan()` will error for undefined inputs (e.g. where `cos(expr)` is near zero).
