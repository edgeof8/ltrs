# Letter Algebra: Formal and Evaluational Identities in the Alphabet of Powers

Working draft. The Cosmic Scratchpad session that produced `cQ*e → V+h` and
`(2b)^a → 1024 · t` is Figure 1. Certificates live in
`tests/test_paper_identities.py` and `examples/paper_letter_algebra.cosmic`.

**Target.** *American Mathematical Monthly* (primary), *Mathematics Magazine*
(backup), or arXiv `math.HO` + `cs.SC`.

**MSC (provisional).** 11A63 (radix representation), 13F20 (polynomial rings),
68W30 (symbolic computation).

## Abstract

We treat the Latin letters as named monomials in \(\mathbb{Z}[X]\), evaluated
at an integer base \(B \ge 2\). Concatenation of letters is addition of
monomials, never multiplication. In this notation two classical facts become
typographic. First, multiplying a sparse sum by a letter is a translation of
the alphabet: \((Q+c)\cdot e = V+h\). Second, raising a scaled letter to a
letter power peels the coefficient off as an ordinary integer in front of a
monomial: \((2b)^a = 2^a\cdot b^a\), which at \(B=10\) is \(1024\cdot t\). We
split identities into three layers — formal in \(\mathbb{Z}[X]\), covariant
after evaluation at every \(B\), and named only at a particular base — and
certify each layer by canonical polynomial equality, without expanding
astronomical digit strings.

## 1. Letters as monomials

Fix an integer \(B \ge 2\), the *calculator base*. Write \(X\) for an
indeterminate. The *rank map* \(r\) sends

- \(a,\dots,y\) to \(1,\dots,25\),
- \(A,\dots,Y\) to \(26,\dots,50\),
- \(Z\) (and the alias \(z\)) to \(100\).

The *letter embedding* is the map \(\varphi\) from letters to \(\mathbb{Z}[X]\)
given by \(\varphi(\ell) = X^{r(\ell)}\). Evaluation \(\mathrm{ev}_B : \mathbb{Z}[X] \to \mathbb{Z}\)
is \(p \mapsto p(B)\). The number a letter *means* is
\(\mathrm{ev}_B(\varphi(\ell)) = B^{r(\ell)}\). In base ten, \(a=10\), \(b=100\),
\(c=10^3\), \(e=10^5\), \(q=10^{17}\), \(t=10^{20}\), \(O=10^{40}\), \(Q=10^{42}\),
\(h=10^8\), \(V=10^{47}\), \(Z=10^{100}\).

A general AoP value is a sparse polynomial
\(p = c_0 + \sum_i c_i X^{e_i}\) with \(c_i \in \mathbb{Z}\) and \(e_i \ge 1\).
*Carry* (canonical form) rewrites any such \(p\) so that every coefficient
lies in \(\{0,1,\dots,B-1\}\). After carry, \(\mathrm{ev}_B\) is injective on
canonical polynomials: this is ordinary uniqueness of base-\(B\) expansions.

The calculator performs arithmetic in \(\mathbb{Z}[X]\) and only asks
\(\mathrm{ev}_B\) for a decimal string in **num** mode. Equality `==` compares
canonical polynomials of the same base. That is the certificate relation used
below. It is *not* a comparison of decimal dumps.

## 2. Juxtaposition is addition

**Theorem 1 (words are sparse sums).** A finite word in letters and
digit-letter chunks denotes the sum of its chunks. In particular, for letters
\(\alpha,\beta\),

\[
\alpha\beta \;=\; \alpha + \beta \;=\; X^{r(\alpha)} + X^{r(\beta)}.
\]

Juxtaposition never multiplies. Multiplication is the operator \(*\).

*Proof.* This is the grammar of the language. The content is that the free
commutative monoid on the alphabet, sent by \(\varphi\), lands in the additive
monoid of \(\mathbb{Z}[X]\). \(\square\)

**Certificate.** `cQ == Q + c` evaluates to `1`. The word \(cQ\) is the
two-spike polynomial \(X^{42}+X^3\).

The parser treats a glued block such as `2b` or `cQ` as a *single* literal,
so `2b^a` is \((2b)^a\) and `cQ*e` is \((c+Q)\cdot e\). That parsing is part
of the notation, not an accident of precedence.

## 3. Translation of the alphabet

**Theorem 2 (letter multiplication is rank addition).** For letters
\(\alpha,\beta\),

\[
\alpha * \beta \;=\; X^{r(\alpha)+r(\beta)}.
\]

If \(r(\alpha)+r(\beta)\) is itself a named rank, the product *is* that
letter. In base-independent form: \(a*b=c\), \(e*Q=V\), \(e*c=h\).

*Proof.* \(\varphi(\alpha)\varphi(\beta) = X^{r(\alpha)} X^{r(\beta)} = X^{r(\alpha)+r(\beta)}\). \(\square\)

**Theorem 3 (translation).** Let \(w = \sum_i \ell_i\) be a sum of letters and
let \(\varepsilon\) be a letter. Then

\[
w * \varepsilon \;=\; \sum_i \ell_i'
\]

where \(r(\ell_i') = r(\ell_i) + r(\varepsilon)\). In the running example,

\[
(Q+c)\cdot e \;=\; V+h.
\]

*Proof.* Distribute and apply Theorem 2:
\(r(Q)+r(e)=42+5=47=r(V)\) and \(r(c)+r(e)=3+5=8=r(h)\). \(\square\)

**Certificate.** `cQ * e == V + h` and `cQ * 2e == 2*(V+h)`.

The second identity is the first with a scaled letter: \(2e = 2\cdot X^5\).
The engine may store the left side as the factored pair \(2\cdot(V+h)\) and
the right side as the distributed polynomial \(2V+2h\). Canonical `==`
identifies them (Theorem 7). The **aop** printer still shows `2 * (V + h)`
on the left — that is the figure, not a disagreement.

This is the first figure. In **num** mode the same identity is a digit string
that begins `100` and ends `01000,00000`: the two spikes have moved five
decimal places. The aop line underneath *names* the move.

The rank map is a homomorphism from the multiplicative monoid of letters
(under `*`) to \((\mathbb{N},+)\). Translation by \(\varepsilon\) is the
action of adding \(r(\varepsilon)\) on ranks, hence a shift of the alphabet.
The same action on a sparse sum is Theorem 3.

## 4. Support gaps and carry

**Theorem 4 (support gap).** Let \(p,q \in \mathbb{Z}[X]\) be canonical, with
\(\operatorname{supp}(p)\) and \(\operatorname{supp}(q)\) disjoint, and
\(\min\operatorname{supp}(p) > \max\operatorname{supp}(q)\). Then \(p+q\) is
already canonical, and the base-\(B\) digit string of \(\mathrm{ev}_B(p+q)\)
is the digit string of \(\mathrm{ev}_B(p)\) followed by exactly
\(\min\operatorname{supp}(p) - \mathrm{width}(q)\) zeros, followed by the
digit string of \(\mathrm{ev}_B(q)\). In particular there is no carry from
\(q\) into \(p\).

*Sketch.* Canonical form only carries when a coefficient is \(\ge B\). Disjoint
supports add coefficientwise with no collision, so no carry is created.
The decimal (or base-\(B\)) layout of a polynomial is digits sitting at
place-values \(B^e\) for \(e\) in the support; a gap in support is a run of
zeros. \(\square\)

For \(Q+c\) the gap is \(42-3=39\) place-values. The five-digit grouping of
**num** mode is a visual ruler for that desert. This is why \(cQ\) looks like
a `100` and a `01000` with nothing in between, and why adding \(c\) to \(Q\)
does not perturb the high spike.

Carry *does* matter for identities such as `10 == a` (in base ten): the
constant \(10\) is rewritten as \(X^1\). Formal division in \(\mathbb{Z}[X]\)
and integer division after carry can therefore disagree about the *route*,
even when they agree about the integer quotient. That distinction belongs in
a remark, not the lead.

## 5. The coefficient-power law, and two presentations

**Theorem 5 (coefficient-power).** Let \(k \in \mathbb{Z}\) and let
\(n,m \ge 0\). After evaluation at \(B\),

\[
\bigl(k \cdot B^n\bigr)^{B^m} \;=\; k^{B^m} \cdot B^{n B^m}.
\]

In letters: \((kb)^{B^m}\) with \(r(b)=n\) is \(k^{B^m}\) times the monomial
of rank \(n B^m\). Taking \(k=2\), \(n=2\), \(m=1\):

\[
(2b)^a \;=\; 2^a \cdot b^a.
\]

*Proof.* \((k B^n)^{B^m} = k^{B^m} (B^n)^{B^m} = k^{B^m} B^{n B^m}\). \(\square\)

This identity is *not* an identity in \(\mathbb{Z}[X]\). The exponent \(a\)
is the integer \(B\), not the indeterminate. It is nevertheless true for
every \(B \ge 2\). Call such identities *base-covariant*.

At \(B=10\), \(2^a = 2^{10} = 1024\) and \(b^a = (10^2)^{10} = 10^{20} = t\),
so \((2b)^a = 1024 \cdot t\). Doubling the exponent,
\((2b)^{2a} = 2^{20} \cdot b^{2a} = 1048576 \cdot O\). Binary powers appear as
coefficients of decimal monomials. That is the second figure.

The engine stores a value as a pair \((k, p)\): a leading coefficient times a
sparse polynomial. Raising the scaled monomial \(2b = 2\cdot X^2\) to the
tenth power keeps the factor: **aop** prints `1024 * (t)`. Multiplying the
already-carried integer \(2^a\) by \(t\) distributes that factor and carries:
**aop** prints `w + 2*u + 4*t`. **num** mode of both is
`1024,00000,00000,00000,00000`. They are the same integer in two
presentations.

**Lemma (digit expansion of a scaled monomial).** For \(k \ge 0\) and
\(e \ge 0\), if \(k = \sum_{i=0}^d k_i B^i\) is the canonical base-\(B\)
expansion of \(k\), then

\[
k \cdot X^e \;=\; \sum_{i=0}^d k_i X^{e+i}
\]

in \(\mathbb{Z}[X]/(X-B)\) after carry. At \(B=10\), \(k=1024\), \(e=20\),
this is \(1024\cdot t = w + 2u + 4t\).

*Proof.* Carry is the rewriting \(B^i X^e = X^{e+i}\) in the quotient by
\(X-B\). Apply it to each digit of \(k\). \(\square\)

**Certificate.** `(2b)^a == 2^a * (b^a)` and `2b^a == 1024 * t` both
evaluate to `1`. The **aop** strings remain distinct: that is the lemma,
not a failure of the identity. Subtraction of two presentations is not
the certificate; `==` is. (Adding two stored pairs still goes through a
separate distribute-and-carry in the arithmetic engine.)

## 6. Formal versus evaluational: base change as experiment

**Definition.** An identity \(L = R\) written in letters is

- *Layer I (formal)* if it holds in \(\mathbb{Z}[X]\) before evaluation
  (Theorems 1–3);
- *Layer II (covariant)* if \(\mathrm{ev}_B(L)=\mathrm{ev}_B(R)\) for every
  \(B \ge 2\), while the two sides need not be the same element of
  \(\mathbb{Z}[X]\) before the exponent is evaluated (Theorem 5) — after
  canonical presentation they still compare equal;
- *Layer III (named)* if it uses a letter or a decimal numeral on the
  right-hand side whose rank (or value) equals a \(B\)-dependent quantity,
  so it holds only for particular \(B\) (Theorem 6).

The same scratchpad, re-evaluated at a new base, is the experiment that
separates the layers. Changing the base does not convert a finished decimal
dump; it reinterprets every letter as a power of the new \(B\).

**Theorem 6 (naming at base ten).** The following are equivalent to \(B=10\):

1. \(b^a = t\), because \(b^a = B^{2B}\) and \(t = B^{20}\);
2. \(b^{2a} = O\), because \(2B\cdot B = 40\);
3. \(2^a = 1024\).

*Proof.* Immediate from the rank map and Theorem 5. \(\square\)

### Figure 3. The same certificates at \(B=2\) and \(B=16\)

At every base the Layer I and Layer II certificates remain `1`. The Layer III
certificates become `0`. The **aop** line of the *value* \(b^a\) shows where
the name went.

| Identity | Layer | \(B=2\) | \(B=10\) | \(B=16\) |
| --- | --- | --- | --- | --- |
| `cQ * e == V + h` | I | 1 | 1 | 1 |
| `(2b)^a == 2^a * (b^a)` | II | 1 | 1 | 1 |
| `b^a == t` | III | 0 | 1 | 0 |
| `2^a == 1024` | III | 0 | 1 | 0 |
| `2b^a == 1024 * t` | III | 0 | 1 | 0 |

The values themselves, not the certificates:

| Expression | \(B=2\) | \(B=10\) | \(B=16\) |
| --- | --- | --- | --- |
| \(a\) | \(2\), aop `a` | \(10\), aop `a` | \(16\), aop `a` |
| \(b^a\) | \(16\), aop `d` | \(10^{20}\), aop `t` | \(16^{32}\), aop `G` |
| \(t\) | \(2^{20}\), aop `t` | \(10^{20}\), aop `t` | \(16^{20}\), aop `t` |
| \(2^a\) | \(4\), aop `b` | \(1024\), aop `c + 2*a + 4` | \(65536\), aop `d` |
| \((2b)^a\) | \(64\), aop `4 * (d)` | \(1024\cdot 10^{20}\), aop `1024 * (t)` | \(65536\cdot 16^{32}\), aop `65536 * (G)` |
| \(2^a\cdot b^a\) | \(64\), aop `f` | same integer, aop `w + 2*u + 4*t` | same integer, aop `K` |

**Reading the table.** Letters name *ranks*, not decimal numbers. At \(B=2\),
\(b^a = (2^2)^2 = 2^4 = d\), while \(t\) is still the letter of rank \(20\).
The identity \(b^a = t\) asked a rank-\(20\) letter to equal a rank that
depends on \(B\). It fails as soon as \(2B \ne 20\). The numeral `1024` is
the same kind of object: it is \(2^{10}\), hence Layer III.

Layer II never mentions those names. \((2b)^a = 2^a \cdot b^a\) holds at
\(B=2\) as \(64=64\), and at \(B=16\) as two forty-digit integers that
`==` identifies without printing them.

**Two presentations, again.** At \(B=2\) the factored form of \((2b)^a\) is
`4 * (d)` and the carried form is `f`, because \(4\cdot X^4 = X^6\) after
carry in base \(2\). At \(B=16\) the coefficient \(2^{16}=65536=16^4\) is
itself a monomial, so `65536 * (G)` carries all the way to the single letter
`K` (rank \(32+4=36\)). At \(B=10\) the coefficient \(1024\) is *not* a
power of ten, so the factored line `1024 * (t)` and the carried line
`w + 2*u + 4*t` remain visibly different. Canonical `==` identifies all
three pairs (Theorem 7). The printer is allowed to show the factor; the
certificate is not allowed to care.

**Remark (when \(2^B\) is a monomial).** \(2^B = B^k\) for an integer
\(k \ge 0\) if and only if \(B = 2^{2^m}\) for some \(m \ge 0\)
(\(B = 2, 4, 16, 256, \ldots\)). In that case \(2^a\) is a unit monomial and
the two **aop** presentations of \((2b)^a\) collapse to one letter after
carry. Base ten is interesting precisely because it is *not* on that list:
the binary coefficient is forced to sit in front of a decimal monomial, which
is the picture in Figure 2.

*Proof of the remark.* If \(B\) has an odd prime factor then \(B^k\) does too,
while \(2^B\) does not. Write \(B=2^s\). Then \(2^{sk}=2^B\) gives
\(k=2^s/s\), so \(s \mid 2^s\), hence \(s\) is a power of \(2\). \(\square\)

Notebooks: `examples/paper_letter_algebra.cosmic` (base 10, Figures 1–2) and
`examples/paper_letter_algebra_base2.cosmic` (Figure 3). The same identities
are locked in `tests/test_paper_identities.py` at bases 2, 10, and 16.

## 7. Canonical presentation, and certificates without digits

An AoP value is a pair \((k,p) \in \mathbb{Z} \times \mathbb{Z}[X]\). The
empty polynomial is the unit for multiplication by \(k\): it denotes the
constant \(k\), equivalently \(k X^0\). Write \(D(k,p) = k\cdot p \in
\mathbb{Z}[X]\) for the *distributed* polynomial, and write \(C\) for carry
into digits in \(\{0,1,\dots,B-1\}\).

**Theorem 7 (canonical presentation).** For non-negative values, \(C(D(k,p))\)
is the unique canonical base-\(B\) expansion of the integer \(k\cdot p(B)\).
In particular

\[
(k,p) \sim (k',p') \quad\text{iff}\quad C(D(k,p)) = C(D(k',p'))
\]

if and only if \(\mathrm{ev}_B(k p) = \mathrm{ev}_B(k' p')\). The relation
\(\sim\) does not require writing that integer.

*Proof.* Uniqueness of base-\(B\) expansions of non-negative integers. Carry
is exactly the rewriting \(c X^e \mapsto (c \bmod B) X^e + \lfloor c/B\rfloor
X^{e+1}\) until every coefficient is a digit. Two polynomials with digits in
\(\{0,\ldots,B-1\}\) evaluate equally iff they are identical. \(\square\)

The engine's `==` is \(\sim\). **aop** mode prints the stored pair \((k,p)\)
without forcing \(C\circ D\), which is why `(2b)^a` still reads `1024 * (t)`
while `2^a * (b^a)` reads `w + 2*u + 4*t`. The certificate does not care.
**num** mode is \(\mathrm{ev}_B\), used for figures, not for equality.

A *proof notebook* is a Cosmic Scratchpad file whose nodes are lemmas and
whose `==` nodes are certificates. `examples/paper_letter_algebra.cosmic`
is the notebook for Theorems 1–7. `tests/test_paper_identities.py` is the
same notebook as unit tests, including bases 2 and 16 as Figure 3.

**Parser note.** Certificates of the form `cQ == Q + c` require `==` to
bind looser than `+`. That is the language (see the spec). Without it,
the Pratt parser reads `(cQ == Q) + c` and returns the letter `c`.

## 8. What this paper is not

Hyperpower collapse — \(Z^e = a^g\) at base ten, without writing
\(10^{10^7}\) digits — is the companion note
`docs/papers/hyperpower-collapse.md`. The multinomial theorem and infix
gcd of letters remain sequels after that.

We do not claim a new theorem of number theory. We claim a language in
which two classical identities are *seen*, a three-layer split that base
change makes experimental, and a certificate relation that does not
require writing the numbers the identities are about.

## Production notes

- **Figures.** Fig. 1: translation nodes (`c`, `q`, `cQ`, `cQ*e`, `cQ*2e`).
  Fig. 2: coefficient-power nodes (`b^a`, `b^2a`, `2b^a`, `2b^2a`).
  Fig. 3: `examples/paper_letter_algebra_base2.cosmic` plus the §6 table
  at bases 2, 10, 16.
- **Voice.** Write as mathematics with an instrument, not as a description
  of software. Name the engine once, in §7.
- **LaTeX.** `docs/papers/letter-algebra.tex` is the Monthly manuscript
  (generic `article` class, theorem–proof, three figures, one certificate
  table). Author names are omitted for double-anonymous review; use
  `docs/papers/letter-algebra-title.tex` as the separate title page.
  Drop in `maa-monthly.sty` from maa.org if desired; the Monthly also
  accepts this generic format.
