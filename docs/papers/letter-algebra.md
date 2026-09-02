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

This is the first figure. In **num** mode the same identity is a digit string
that begins `100` and ends `01000,00000`: the two spikes have moved five
decimal places. The aop line underneath *names* the move.

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

**Certificate (today).** The **num** strings agree, in every base. The **aop**
strings disagree at base ten: factored `1024 * (t)` versus carried
`w + 2*u + 4*t`. Structural `==` on the pair \((k,p)\) returns `0`. Making
`==` compare distributed-then-carried polynomials is the next instrument
change the paper needs; `as_distributed_poly` already exists in the Rust
core.

## 6. Formal versus evaluational

**Definition.** An identity \(L = R\) written in letters is

- *Layer I (formal)* if it holds in \(\mathbb{Z}[X]\) before evaluation
  (Theorems 1–3);
- *Layer II (covariant)* if \(\mathrm{ev}_B(L)=\mathrm{ev}_B(R)\) for every
  \(B \ge 2\), but \(L\) and \(R\) are not equal as polynomials
  (Theorem 5);
- *Layer III (named)* if it uses a letter on the right-hand side whose rank
  equals a \(B\)-dependent quantity, so it holds only for particular \(B\)
  (the naming step in Theorem 6).

**Theorem 6 (naming at base ten).** The following are equivalent to \(B=10\):

1. \(b^a = t\) (because \(b^a = B^{2B}\) and \(t = B^{20}\));
2. \(b^{2a} = O\) (because \(2B\cdot B = 40\));
3. \(2^a = 1024\).

*Proof.* Immediate from the rank map and Theorem 5. \(\square\)

**Experiment.** The same scratchpad at `/setbase 2` keeps
`cQ * e == V + h` (Layer I: both sides are \(X^{47}+X^8\)) and
`(2b)^a == 2^a * (b^a)` (Layer II), and breaks `b^a == t` (Layer III:
left is \(B^{2B} = 2^4 = 16\), right is \(2^{20}\)). Base change is a
laboratory, not a display option.

## 7. Certificates without digits

Let \(\equiv\) denote equality of the stored pair \((k,p)\). The engine's
`==` is \(\equiv\) today. For Layer I both sides are already in the same
presentation, so \(\equiv\) is the theorem. For Layer II, \(\equiv\) is
strictly finer than integer equality: it distinguishes factored form from
carried form. Integer equality is recovered from matching **num** strings,
or (once the instrument is upgraded) from comparing
`as_distributed_poly` after carry, still without expanding to a Python
`int`.

A *proof notebook* is a Cosmic Scratchpad file whose nodes are lemmas and
whose `==` nodes are certificates. `examples/paper_letter_algebra.cosmic`
is the notebook for Theorems 1–6. `tests/test_paper_identities.py` is the
same notebook as unit tests, including an explicit base-2 counterexample
for every Layer III claim, and a record that `(2b)^a == 1024 * t` is
currently `0` while the **num** strings match.

**Parser note.** Certificates of the form `cQ == Q + c` require `==` to
bind looser than `+`. That is now the language (see the spec). Without it,
the Pratt parser reads `(cQ == Q) + c` and returns the letter `c`.

## 8. What this paper is not

The multinomial theorem, hyperpower collapse \((B^p)^{B^q} = B^{p B^q}\)
(so \(Z^e\) formats as \(a^g\)), and \(\gcd(B^i,B^j)=B^{\min(i,j)}\) (so
`Z gcd Y` would be `Y`) are all native to the same notation. They are
sequels. The first two are already visible in the engine; infix `gcd` is
not yet implemented. None of them is needed to justify Theorems 1–6.

We do not claim a new theorem of number theory. We claim a language in
which two classical identities are *seen*, a three-layer split that base
change makes experimental, and a certificate relation that does not
require writing the numbers the identities are about.

## Production notes

- **Figures.** Fig. 1: translation nodes (`c`, `q`, `cQ`, `cQ*e`, `cQ*2e`).
  Fig. 2: coefficient-power nodes (`b^a`, `b^2a`, `2b^a`, `2b^2a`).
  Fig. 3: the same file at base 2, with Layer III certificates failed.
- **Voice.** Write as mathematics with an instrument, not as a description
  of software. Name the engine once, in §7.
- **Next prose to finish.** §3 and §5 from the existing screenshots; then
  §6 with the base-2 run.
- **Instrument.** Make `==` compare distributed-then-carried polynomials so
  Layer II certificates become `==` nodes. Until then, certify Layer II by
  matching **num** strings and recording the two **aop** presentations.
- **LaTeX.** Convert this file once §1–7 are stable. Monthly style,
  theorem–proof, three figures, one table of certificates.
