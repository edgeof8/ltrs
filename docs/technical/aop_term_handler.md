# aop_term_handler.py

Handles AoP term evaluation and simplification.

## Key Functions

### `evaluate_word(word: str, base: int) -> AoPValue`

Calculates the value of a word:

1. Maps each letter to its exponent
2. Sums exponents
3. Returns `(1.0, total_exponent)`

### `create_term_from_letter(letter: str, base: int) -> AoPTerm`

Creates term from single letter:

- `a` → `(1.0, 1)`
- `B` → `(1.0, 28)`

### `create_term_from_coeff_letter(coeff: float, letter: str, base: int) -> AoPTerm`

Creates term like `2b` → `(2.0, 2)`

### `simplify_term(term: AoPTerm, base: int) -> AoPTerm`

Simplifies terms where coefficient is a power of base:

- `(10.0, 3)` → `(1.0, 4)` (10c becomes d)

## Letter Mapping

- Lowercase a-z: exponents 1-26
- Uppercase A-Y: exponents 27-51
- Case-insensitive

## Example Usage

```python
from aopl_python_impl.aop_term_handler import evaluate_word

# Evaluate "cat" in base 10
value = evaluate_word("cat", 10)  # (1.0, 24)
