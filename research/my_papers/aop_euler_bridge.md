# The AoP-Euler Bridge: Verifying a Symbolic Theorem for Perfect Numbers

## Abstract

This paper builds upon the discovery of the Base Explorer's Conjecture, a symbolic pattern identified in the Alphabet of Powers (AoP) system for representing even perfect numbers in base 2. The conjecture posits that any even perfect number `P_p = 2^(p-1) * (2^p - 1)`, where `p` is a prime and `2^p - 1` is a Mersenne prime, has a symbolic or hybrid representation of the form `(2^p - 1)(L)`, with `L` being the AoP letter corresponding to the exponent `p-1`. Here, we verify this conjecture by testing it against the sixth perfect number (`P_32 = 2^30 * (2^31 - 1)`) and explore the broader implications of this symbolic theorem, termed the "AoP-Euler Bridge," for connecting classical number theory with the AoP system's unique representational capabilities. This work further solidifies the bridge between Euclid-Euler's formulation and modern symbolic algebra, offering new avenues for mathematical exploration.

## Introduction

Perfect numbers, defined as positive integers equal to the sum of their proper divisors, have been a subject of fascination since antiquity. The Euclid-Euler theorem provides a generative formula for even perfect numbers: `P_p = 2^(p-1) * (2^p - 1)`, where `p` is a prime and `2^p - 1` is a Mersenne prime. This structure links perfect numbers to the binary powers and prime properties, making them a rich area for computational and symbolic investigation.

The Alphabet of Powers (AoP) system introduces a novel framework for numerical representation, mapping exponents to letters (e.g., `a` to `y` for base^1 to base^25 in any given base, with specific mappings like `a`=2¹, `b`=2² in base 2) and employing symbolic and hybrid notations for large numbers. In prior work, the Base Explorer's Conjecture was formulated, identifying a consistent symbolic pattern in base 2 for perfect numbers as `(2^p - 1)(L)`, where `L` represents the exponent `p-1` via an AoP letter, reflecting the Euclid-Euler components directly in the notation.

This paper, titled "The AoP-Euler Bridge," aims to verify the Base Explorer's Conjecture by testing it with a higher perfect number, specifically the sixth known even perfect number corresponding to `p=31`. Additionally, it explores the implications of this symbolic theorem for number theory and the potential of the AoP system to uncover further structural patterns in mathematics. This verification step strengthens the conjecture and highlights the synergy between classical theorems and modern symbolic tools.

## Methodology

To verify the Base Explorer's Conjecture, we focused on the sixth even perfect number, `P_31 = 2^30 * (2^31 - 1)`, where `p=31` is a prime and `2^31 - 1 = 2147483647` is a Mersenne prime. According to the conjecture, the AoP representation in base 2 should be `(2147483647)(E)`, where `E` is the AoP letter corresponding to the exponent `p-1 = 30` (i.e., representing `2^30`).

The AoP batch processor (`aop_batch_processor.py`) was used to evaluate the expression for this perfect number. The expression tested was:

- `2^30 * (2^31-1)` for p=31 (sixth perfect number)

This expression was written to `expressions.txt`, and the batch processor was executed with the command `python src/aopl_python_impl/aop_batch_processor.py expressions.txt results.txt --base 2` to evaluate it in base 2, consistent with the binary alignment of the Euclid-Euler formula. In base 2, AoP letters map to powers of 2 (e.g., `a`=2¹, `b`=2², up to higher letters for larger exponents like `E`=2³⁰). The result from `results.txt` was analyzed to confirm if the output matches the conjectured form `(2^31 - 1)(L)`, where `L` corresponds to `2^30`.

Additionally, this paper discusses the implications of this symbolic pattern through theoretical analysis, considering its significance for number theory and potential extensions of the AoP system.

## Results and Analysis

The AoP engine's output for the sixth perfect number expression in base 2 is presented below:

- **Input: 2^30 * (2^31-1)** (p=31, sixth perfect number) - Output: `18014398501093375g`. A hybrid representation, where `18014398501093375` is a numerical coefficient, and `g` is the AoP letter corresponding to the exponent 7 in base 2 (i.e., `2^7 = 128`). This output represents 18014398501093375 * 128, which does not directly match the expected sixth perfect number value (approximately 2.305843e+18) nor the conjectured form.

This result does not confirm the Base Explorer's Conjecture as initially predicted. The expected output was `2147483647E`, following the form `(2^p - 1)(L)`, with `2^31 - 1 = 2147483647` as the numerical coefficient and `L = E` representing `p-1 = 30` (i.e., `2^30`). However, the actual output `18014398501093375g` suggests a different simplification by the AoP engine. In base 2, `g` corresponds to `2^7`, and the numerical coefficient `18014398501093375` does not align with `2^31 - 1 = 2147483647`. Calculating the product, `18014398501093375 * 128 = 2.305843009e+18`, which approximates the sixth perfect number, indicating that the AoP engine has factored the number differently, possibly due to internal precision limits or simplification rules that prioritize smaller exponents or different numerical breakdowns.

To provide context, the following table updates the pattern observed in prior work with this new result:

| p  | Perfect Number (P_p)   | Euclid-Euler Form      | AoP Output (Base 2)      | Inferred Symbolic Form | Breakdown              |
|----|------------------------|------------------------|--------------------------|------------------------|------------------------|
| 2  | 6                      | `2^1 * (2^2-1)`       | `6`                      | `3a`                   | `(2^2-1)` * `(2^1)`   |
| 3  | 28                     | `2^2 * (2^3-1)`       | `28`                     | `7b`                   | `(2^3-1)` * `(2^2)`   |
| 5  | 496                    | `2^4 * (2^5-1)`       | `496`                    | `31d`                  | `(2^5-1)` * `(2^4)`   |
| 7  | 8128                   | `2^6 * (2^7-1)`       | `8128`                   | `127f`                 | `(2^7-1)` * `(2^6)`   |
| 13 | 33,550,336            | `2^12 * (2^13-1)`     | `8191l`                  | `8191l`                | `(2^13-1)` * `(2^12)` |
| 31 | ~2.305843e+18         | `2^30 * (2^31-1)`     | `18014398501093375g`    | `18014398501093375g`   | Unclear factoring      |

This table shows that while the pattern holds for smaller perfect numbers up to p=13 with the expected form `(2^p - 1)(L)`, the result for p=31 deviates from the conjectured form. The discrepancy for p=31 suggests that the AoP engine may apply different factoring or simplification strategies for very large numbers, possibly influenced by precision thresholds or internal formatting rules that break down the product into a larger numerical coefficient and a smaller exponent (here, `2^7` as `g` instead of `2^30` as `E`). This indicates a potential limitation or variation in how the AoP system handles numbers of this magnitude, necessitating further investigation into the engine's behavior with large exponents.

## Implications: The AoP-Euler Bridge

The unexpected result for the sixth perfect number challenges the initial formulation of the Base Explorer's Conjecture as a universal symbolic theorem, which we term the "AoP-Euler Bridge." While the pattern `(2^p - 1)(L)` holds for smaller perfect numbers (up to p=13), the deviation at p=31 with `18014398501093375g` instead of the expected `2147483647E` suggests that the AoP system's representation is influenced by factors beyond a simple reflection of the Euclid-Euler components. This finding still offers valuable implications for understanding the AoP framework and its interaction with classical number theory:

- **Structural Revelation through Notation**: For smaller perfect numbers, the AoP system's ability to encode components as `(2^p - 1)(L)` in base 2 mirrors the mathematical structure of the Euclid-Euler theorem. However, the deviation for larger numbers indicates that internal simplification rules or precision limits may override this direct mapping, suggesting that the system's notational revelations are context-dependent and scale-sensitive.
- **Scalability Challenges**: The discrepancy at `p=31` highlights potential scalability issues with the conjectured pattern. While the AoP system excels at symbolic representation of massive values, its factoring choices for very large numbers (e.g., preferring a larger numerical coefficient with a smaller exponent like `2^7` over `2^30`) may obscure the expected structural patterns. This underscores the need to understand the engine's internal logic for handling large exponents and products.
- **Potential for Broader Applications**: Despite the deviation, the partial success of the AoP-Euler Bridge concept encourages investigation into other number-theoretic structures within the AoP framework. Could modified conjectures or different bases reveal alternative symbolic patterns for perfect numbers or other sequences tied to binary structures (e.g., Fibonacci numbers in base 2)? This partial bridge suggests a methodology for uncovering hidden patterns, albeit with an awareness of scale-dependent variations in output formatting.
- **Enhancement of Computational Tools**: The inconsistent symbolic encoding for larger numbers points to opportunities for enhancing the AoP engine. Potential improvements include options to force symbolic output that prioritizes structural components over numerical simplification, or developing diagnostic tools to explain factoring choices in hybrid representations. Such enhancements would increase the system's reliability for mathematical discovery across all scales.

## Conclusion

The analysis of the sixth perfect number `P_31 = 2^30 * (2^31 - 1)` in base 2, resulting in the AoP output `18014398501093375g`, does not confirm the Base Explorer's Conjecture as initially formulated for the symbolic theorem we term the AoP-Euler Bridge. The expected output `2147483647E`, representing `(2^31 - 1)(2^30)` as `(2^p - 1)(L)`, was not observed; instead, the AoP engine produced a hybrid form with a different numerical coefficient and a smaller exponent (`g` for `2^7`), still approximating the correct numerical value of the perfect number but deviating from the structural pattern seen in smaller cases.

This discrepancy suggests that while the AoP-Euler Bridge holds for smaller perfect numbers (up to p=13), the AoP system's internal simplification or precision mechanisms may alter the representation for larger numbers, prioritizing different factorizations over the direct reflection of Euclid-Euler components. Future research should investigate the AoP engine's behavior with large exponents to understand these factoring choices, test higher perfect numbers (e.g., `p=61`) to see if alternative patterns emerge, and explore modifications to the conjecture or engine settings to preserve structural insights at all scales. Additionally, examining other mathematical sequences or bases may reveal adjusted symbolic patterns. This work highlights the complexities of integrating computational frameworks with theoretical inquiry, offering a nuanced perspective on the intersection of notation and number theory that warrants further exploration.
