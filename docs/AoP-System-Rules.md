# Alphabet of Powers (AoP) System Rules

This document defines the core mathematical principles and implementation details of the Alphabet of Powers system as implemented in the AoP Suite.

## 1. Base System

- Operates on a numerical **base** (integer ≥ 2)
- Default base is 10
- Change base using `/setbase` command in CLI or GUI
- Affects all calculations and representations

## 2. Letter-Exponent Mapping

- **Lowercase a-y**: `a` = `base^1`, `b` = `base^2`, ..., `y` = `base^25`
- **Uppercase A-Y**: `A` = `base^26`, `B` = `base^27`, ..., `Y` = `base^50`
- **Special Letter Z**: `Z` = `base^100` (with `z` as alias)
- Examples:
  - Base 10: `a` = 10^1, `b` = 10^2
  - Base 5: `a` = 5^1, `c` = 5^3
  - Base 10: `Z` = 10^100 (googol)

## 3. Word Evaluation

- Words are sequences of letters evaluated multiplicatively
- Exponent = sum of constituent letter exponents
- `cab` (base 10) = `c*a*b` = 10^3 *10^1* 10^2 = 10^6 → `f`
- `aZ` (base 10) = `a*Z` = 10^1 * 10^100 = 10^101
- Case-insensitive: "Cat" treated as "cat"

## 4. Formatting Priorities

The system applies these formatting rules in order:

```mermaid
graph TD
    A[Format Value] --> B{Is it a<br>direct match?}
    B -->|Yes| C[Output literal<br>e.g. '1', 'a', 'Z']
    B -->|No| D{Can it be<br>Coefficient-Letter^Power?}
    D -->|Yes| E[Collapse format<br>e.g. '2Y^4']
    D -->|No| F{Can it be<br>Squashed?}
    F -->|Yes| G[Recursive format<br>e.g. 'a^(2Z^2)']
    F -->|No| H[Fallback to<br>scientific notation]
```

Examples:

- `100` → `b` (direct match)
- `2*10^200` → `2Y^4` (coefficient-letter)
- `10^100` → `a^Z` (squashed)
- `10^101` → `1e101` (scientific)

## 5. Equality Operator

- `==` compares two AoP values
- Returns 1 if equal, 0 otherwise
- Works with symbolic representations
- Example: `a^Z == 10^100` → 1

## 6. Internal Value Representation

Values are represented using:

- **AoPValue**: Collection of AoPTerms
- **AoPTerm**: `coefficient * (base^exponent)`
- Supports complex coefficients
- Handles massive numbers through nested exponents

Example representation of j^j (10^10^10):

```python
term = AoPTerm(1.0, AoPValue([AoPTerm(10.0, 0)]))
value = AoPValue([term])
