# Alphabet of Powers (AoP) System Rules

This document outlines the core rules and definitions of the Alphabet of Powers (AoP) mathematical system as implemented by the `ltrs` calculator.

## 1. Base System

- The AoP system operates on a numerical **base**, an integer ≥ 2.
- Default base is 10.
- Change base in REPL: `/setbase <number>`. Clears all variables.

## 2. Letter-Exponent Mapping

- Lowercase letters: `a` = `base^1`, `b` = `base^2`, ..., `z` = `base^26`
- Uppercase letters: `A` = `base^27`, `B` = `base^28`, ..., `Y` = `base^50`
- Examples:
  - Base 10: `a` = 10^1, `b` = 10^2
  - Base 5: `a` = 5^1, `c` = 5^3

## 3. Word Evaluation

- A "word" is a sequence of letters (e.g., "cat", "dog")
- Exponent: sum of constituent letter exponents
  - `cat` = exponent_c + exponent_a + exponent_t = 3 + 1 + 20 = 24
- Numerical value: `base^word_exponent`
  - Base 10: `cat` = 10^24
- Case-insensitive: "Cat" treated as "cat"

## 4. Internal Value Representation (`AoPValue`)

- AoP values represented as `Ao极

[Response interrupted by a tool use result. Only one tool may be used at a time and should be placed at the end of the message.]
