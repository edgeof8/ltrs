# Hyperpower Collapse in the Alphabet of Powers

Sequel to `letter-algebra.md`. That note was translation and coefficient-power.
This one is what happens when a *letter* is raised to a *letter*. Certificates
live in `tests/test_paper_hyperpower.py` and `examples/paper_hyperpower.cosmic`.
Never ask **num** mode for \(Z^e\): that would request the decimal digits of
\(10^{10^7}\). Canonical `==` never does.

**Target.** A short Monthly note, or a second section of the Letter Algebra
paper if a referee wants them together. MSC 11A63, 11A25.

## Abstract

A letter to a letter power is a monomial whose exponent is a product of ranks.
In the Alphabet of Powers that product often *collapses* to a shorter word:
\(Z^e = a^g\) at base ten, because \(100\cdot 10^5 = 10^7\). We prove the
collapse as an identity in ranks, classify it with the three layers of the
companion note, and certify \(Z^e == a^g\) without expanding the integer.
Juxtaposition in the base of a power is not a product: \((aZ)^b\) is a
binomial expansion, while \((a*Z)^b = a^{d+b}\). Base change again separates
what is formal from what is only a name.

## 1. Monomial hyperpowers

Fix a calculator base \(B \ge 2\). Letters are unit monomials, as in the
companion note: \(\varphi(\ell) = X^{r(\ell)}\), \(\mathrm{ev}_B(p)=p(B)\).

**Theorem 1 (monomial hyperpower).** For ranks \(p,q \ge 0\),

\[
\bigl(B^p\bigr)^{B^q} \;=\; B^{p\, B^q}.
\]

In letters: \(\alpha^\beta = B^{r(\alpha)\, B^{r(\beta)}}\), a unit monomial
of rank \(r(\alpha)\, B^{r(\beta)}\).

*Proof.* Direct. \(\square\)

This is Layer II: true for every \(B\), after letters have become integers.
The engine's pure-symbolic power path stores exactly that monomial,
\(\{p\cdot B^q : 1\}\), and never asks for the digits of \(B^{p B^q}\).

**Certificate.** `Z^e == a^g` at \(B=10\) (Theorem 2 names the right-hand
side). The same identity written without names is Theorem 1 with
\(p=100\), \(q=5\).

## 2. Collapse: adding logs of ranks

Suppose the rank of the base is itself a power of \(B\), say
\(r(\alpha) = B^s\). Then Theorem 1 gives

\[
\alpha^\beta \;=\; B^{B^s \cdot B^{r(\beta)}} \;=\; B^{B^{s+r(\beta)}}.
\]

If \(s+r(\beta)\) is a named rank \(\gamma\), the **aop** printer writes
\(a^\gamma\). Adding the logarithms of the ranks has *collapsed* a power
into a shorter word. That is the logarithmic shortcut.

At \(B=10\), \(r(Z)=100=10^2\), so \(s=2\). Then:

| Power | Rank product | Named result |
| --- | --- | --- |
| \(Z^a\) | \(100\cdot 10 = 10^3\) | `a^c` |
| \(Z^b\) | \(100\cdot 10^2 = 10^4\) | `a^d` |
| \(Z^c\) | \(100\cdot 10^3 = 10^5\) | `a^e` |
| \(Z^d\) | \(100\cdot 10^4 = 10^6\) | `a^f` |
| \(Z^e\) | \(100\cdot 10^5 = 10^7\) | `a^g` |

**Theorem 2 (named collapse at base ten).** \(Z^e = a^g\) if and only if
\(B=10\). More generally \(Z^\lambda = a^\mu\) for \(\lambda \in \{a,\ldots,e\}\)
and \(\mu\) of rank \(2+r(\lambda)\) if and only if \(r(Z)=B^2\), i.e.
\(B=10\).

*Proof.* \(r(Z)=100\) always (the letter map is fixed). \(100 = B^2\) iff
\(B=10\). The table is Theorem 1 plus that equality. \(\square\)

**Certificate.** `Z^e == a^g`, `Z^a == a^c`, …, `Z^d == a^f` evaluate to `1`
at base 10 and to `0` at bases 2 and 16.

**Figure 1.** The chain \(Z^a, Z^b, Z^c, Z^d, Z^e\) sliding up the alphabet
as `a^c`, `a^d`, `a^e`, `a^f`, `a^g`. Each step adds one to the log-rank.

Y is the counterpoint. \(r(Y)=50\), which is not a power of ten, so

\[
Y^e \;=\; B^{50\cdot B^5} \;=\; B^{5\cdot B^6} \;=\; a^{5f}
\]

at \(B=10\). Certificate: `Y^e == a^(5*f)` is `1`, and `Y^e == a^f` is `0`.
Collapse to a *single* letter requires the rank of the base to be a pure
power of \(B\).

## 3. The inverse name: \(a^b = Z\)

**Theorem 3.** \(a^b = Z\) if and only if \(B=10\).

*Proof.* \(a^b = B^{B^2}\) and \(Z = B^{100}\), so \(B^2=100\). \(\square\)

This is the inverse of the first row of the table in §2, and the same Layer
III naming as \(b^a = t\) in the companion note. Certificate: `a^b == Z`
is `1` at base 10, `0` at bases 2 and 16. At \(B=2\), \(a^b = 2^{4} = d\).
At \(B=16\), \(a^b\) remains nested `a^b` (the exponent \(256\) is not a
named rank).

## 4. Towers

Power is right-associative, so \(a^b^c = a^{(b^c)}\).

**Theorem 4 (tower at base ten).** \(a^b^c = a^{(a^{(2c)})}\) at \(B=10\).

*Proof.* \(b^c = B^{2 B^3} = B^{2000}\), a unit monomial of rank \(2000\).
Then \(a^{(b^c)} = B^{B^{2000}}\), which **aop** writes as \(a^{a^{2000}}\).
The number \(2000\) is \(2c\). \(\square\)

**Certificate.** `a^b^c == a^(a^(2*c))` at base 10. At base 2 the same
expression formats as `a^p` (rank \(2\cdot 2^3 = 16 = p\)), a Layer III
rename.

A taller tower: \(Z^Z = B^{100\cdot B^{100}} = B^{B^{102}} = a^{(a^{(b+2)})}\)
at \(B=10\), because \(102 = b+2\). Certificate: `Z^Z == a^(a^(b + 2))`.

## 5. Product in the base, not juxtaposition

**Theorem 5 (product of letters as base).** For letters \(\alpha_i\) and
exponent \(\beta\),

\[
(\alpha_1 * \cdots * \alpha_n)^\beta \;=\; B^{\bigl(\sum_i r(\alpha_i)\bigr) B^{r(\beta)}}.
\]

At \(B=10\), `(d*o*g)^c = a^(2*d + 6*c)` because
\(r(d)+r(o)+r(g)=4+15+7=26\) and \(26\cdot 10^3 = 26000 = 2\cdot 10^4 + 6\cdot 10^3\).

**Certificate.** `(d*o*g)^c == a^(2*d + 6*c)` and
`(a*Z)^b == a^(d + b)` (ranks \(1+100=101\), times \(10^2\), gives \(10100 = d+b\)).

Juxtaposition is addition, so `(aZ)^b` is \((X + X^{100})^{B^2}\), a binomial
(multinomial) expansion with a hundred terms. It is *not* `(a*Z)^b`. The
companion note's grammar is doing work here: one missed `*` turns a collapse
into a dense polynomial. Do not evaluate `(aZ)^b` in **num** mode.

## 6. Base change

The same three layers apply.

| Identity | Layer | \(B=2\) | \(B=10\) | \(B=16\) |
| --- | --- | --- | --- | --- |
| `Z^e == a^g` | III | 0 | 1 | 0 |
| `a^b == Z` | III | 0 | 1 | 0 |
| `Y^e == a^(5*f)` | II (shape) / III (name \(5f\)) | 0 | 1 | 0 |
| `Z^e == Z^e` | I | 1 | 1 | 1 |

At \(B=2\), Theorem 1 still holds: \(Z^e = B^{100\cdot 2^5} = B^{3200}\), and
\(3200 = 2^{11}+2^{10}+2^7\), so **aop** is `a^(k + j + g)`, not `a^g`.
At \(B=16\), \(100\cdot 16^5\) formats as `a^(6*f + 4*e)`. The collapse
*to the letter g* is a name that lives at base ten, for the same reason
\(b^a = t\) did.

**Remark.** \(r(Z)=100=B^2\) is the whole named-collapse family. Any other
base leaves \(100\) as a mixed digit string in the exponent of \(a\).

## 7. What this note is not

We still do not claim a new theorem of elementary arithmetic. We claim that
the same letter language that made translation typographic makes *iterated
rank multiplication* typographic, and that `==` certifies \(Z^e = a^g\)
without writing \(10^{10^7}\) digits.

Infix gcd of letters (\(\gcd(B^i,B^j)=B^{\min(i,j)}\)) remains a third note.

## Production notes

- **Figures.** Fig. 1: the \(Z^\lambda\) chain collapsing to `a^c`…`a^g`.
  Fig. 2: `a^b == Z` and `Z^Z == a^(a^(b + 2))`. Fig. 3: base 2, where
  `Z^e` is `a^(k + j + g)` and `Z^e == a^g` is `0`.
- **Voice.** Companion to Letter Algebra. Cite that note for ranks,
  juxtaposition, layers, and canonical `==`.
- **Never num.** Certificates are `==` nodes in **aop** (the result is
  `0` or `1`). Evaluating `Z^e` in **num** is the mistake the instrument
  exists to avoid.
