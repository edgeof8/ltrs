# Alphabet of Powers language (spec)

This is the language the calculator actually implements. Arithmetic stays a
sparse polynomial until **num** mode asks for decimal digits.

## Letters and the calculator base

A letter is a power of the current calculator base \(B\) (default \(B = 10\)):

- `a` … `y` are \(B^1\) … \(B^{25}\)
- `A` … `Y` are \(B^{26}\) … \(B^{50}\)
- `Z` and `z` are \(B^{100}\)

So in base 10, `a` is ten, `b` is a hundred, `c` is a thousand, `Z` is
\(10^{100}\). Changing the base changes what the same letter *means*; the
engine re-evaluates the source expression. It does not convert a finished
decimal dump from one base into another.

A digit sequence is an ordinary integer. Scientific `3e3` is parser sugar for
a decimal, not a letter.

## Juxtaposition is addition

Placing letters (and digit-letter chunks) next to each other **adds** them. It
never multiplies.

| Written | Means | Base 10 |
| --- | --- | --- |
| `ba` | `b + a` | 110 |
| `cab` | `c + a + b` | 1110 |
| `2c4a` | `2*c + 4*a` | 2040 |
| `2b` | `2 * b` | 200 |

`ba` is not `b*a`. Multiplication is always an explicit `*`.

Parentheses still group and can imply multiplication in the usual way:
`a(b+c)` is a product.

## Operators

Precedence, high to low: `^` / `**` (right-associative), then `*` and `/`
(left-associative), then `+` and `-`, then `==` (left-associative), then
`=` (right-associative). So `cQ == Q + c` is `cQ == (Q + c)`, not
`(cQ == Q) + c`.

- `*` multiplies polynomials. `a * b` is \(B^1 \cdot B^2 = B^3\), which **aop**
  mode prints as `c`, not `a^3`.
- `^` is power. `a ^ b` is \(B^{B^2} = B^{100}\) in base 10, printed as `Z`.
- `/` is **exact**. The quotient must be an integer (equivalently, the
  polynomial must divide evenly, with a fallback through exact integer
  division when carrying has already rewritten a constant as \(X^1\)).
  `c / a` is `b`. `a / b`, `(a + 1) / a`, and `a / 0` raise `AoPError`.
  There is no truncating integer division and no fraction type.
- `==` compares **canonical polynomials** of the same base: distribute the
  leading coefficient into \(\mathbb{Z}[X]\), carry until digits lie in
  \(\{0,\ldots,B-1\}\), and compare the resulting sparse maps. It does not
  expand either side into a Python `int`. Factored form and carried form of
  the same integer are equal: `(2b)^a == 1024 * t`. After simplify,
  `a == 10` is true in base 10 because `10` is stored as \(X^1\).
- `$name = expr` binds a variable. A trailing `=` with a non-variable left
  side evaluates the left-hand side (`a=` is `a`).

## Two output modes

- **aop:** print with the letter map. A unit monomial \(B^E\) whose exponent
  is in the map is that letter (`a*b` → `c`, `a^b` → `Z`). Exponents outside
  the map stay nested `a^(…)` form.
- **num:** the only place the polynomial is forced into a decimal string.
  Digits are grouped with commas every five characters from the right
  (`100000` → `1,00000`). Commas that sit between digits in **input** are
  ignored, so pasting a grouped result back in is the same number.
  Exponents that do not fit in `u32` fail instead of wrapping to \(B^0\).

## Errors

Library code raises `AoPError`. The CLI prints `Error: …` and exits 1. The
GUI still shows that prefix on the node. Mixed calculator bases on `+`, `-`,
`*`, `/`, or `^` are errors, not panics.
