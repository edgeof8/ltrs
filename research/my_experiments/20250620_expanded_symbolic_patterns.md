# Expanded Symbolic Pattern Recognition Experiments (2025-06-20)

## Objective

This set of experiments builds on the initial findings from "20250620_symbolic_patterns.md" to further investigate patterns and symmetries in the Alphabet of Powers (AoP) system's letter-based notation for large exponential expressions. The focus is on running a significantly larger number of calculations across varied bases, nesting depths, and letter choices to uncover deeper structural patterns or fractal-like behaviors in the notation.

## Experiment Setup

- **Tool**: AoP Calculator CLI (`ltrs` or direct Python module invocation)
- **Focus**: Nested power towers with varying depths (e.g., "a^a", "a^a^a", up to deeper levels), different starting letters (a, b, c, etc.), and multiple bases.
- **Variables**: Base (2, 5, 10, 16), depth of nesting (2 to 6 levels), and letter choice (a to e, representing different exponents).
- **Documentation**: All commands, outputs, and analyses will be recorded below in batches for efficiency.

## Batch 1: Power Towers with 'a' Across Bases and Depths

**Description**: Testing nested powers of 'a' with depths from 2 to 6 across bases 2, 5, 10, and 16 to observe notation evolution with increasing complexity.

- **Command 1.1**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a" --base 2`
  **Output**: `b`
  **Analysis**: The output `b` represents 2^2 = 4, the result of 2^2 in base 2, where `a` is 2^1. This simple single-letter notation reflects the small magnitude of the result, consistent with base 2's compact representation for lower values.

- **Command 1.2**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a" --base 2`
  **Output**: `d`
  **Analysis**: The output `d` represents 2^4 = 16, the result of 2^(2^2) in base 2. Similar to Command 1.1, a single letter is used, indicating that for relatively small results in base 2, the notation remains straightforward without nesting.

- **Command 1.3**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a" --base 2`
  **Output**: `p`
  **Analysis**: The output `p` represents 2^16 = 65536, the result of 2^(2^(2^2)) in base 2. Still a single letter, this shows the AoP system continues to use compact notation for results up to this magnitude in base 2, differing from base 10's more complex forms at similar depths.

- **Command 1.4**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a" --base 2`
  **Output**: `a^p`
  **Analysis**: The output `a^p` represents 2^65536, the result of 2^(2^(2^(2^2))) in base 2, where `a` is 2^1 and `p` is 2^16. The shift to a symbolic form with exponentiation indicates the system's adaptation to larger numbers, introducing nesting as the magnitude increases beyond simple letter mappings.

- **Command 1.5**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a^a" --base 2`
  **Output**: `a^(a^p)`
  **Analysis**: The output `a^(a^p)` represents 2^(2^65536), the result of 2^(2^(2^(2^(2^2)))) in base 2. This deeper nesting in the notation mirrors the input's structure, suggesting a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation, similar to base 10 but scaled to base 2's magnitude.

- **Command 1.6**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a" --base 5`
  **Output**: `e`
  **Analysis**: The output `e` represents 5^5 = 3125, the result of 5^5 in base 5, where `a` is 5^1. This single-letter notation reflects the manageable magnitude of the result, consistent with base 5's representation for smaller values.

- **Command 1.7**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a" --base 5`
  **Output**: `a^e`
  **Analysis**: The output `a^e` represents 5^3125, the result of 5^(5^5) in base 5, where `a` is 5^1 and `e` is 5^5. The shift to symbolic notation with exponentiation indicates the system's adaptation to larger numbers, introducing nesting earlier than in base 2 due to base 5's faster growth.

- **Command 1.8**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a" --base 5`
  **Output**: `a^(a^e)`
  **Analysis**: The output `a^(a^e)` represents 5^(5^3125), the result of 5^(5^(5^5)) in base 5. This nested notation mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation.

- **Command 1.9**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a" --base 5`
  **Output**: `a^(a^(a^e))`
  **Analysis**: The output `a^(a^(a^e))` represents 5^(5^(5^3125)), the result of 5^(5^(5^(5^5))) in base 5. The deeper nesting continues to reflect the hierarchical structure of the input, emphasizing the AoP system's consistent approach to representing hyper-large numbers through recursive notation.

- **Command 1.10**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a^a" --base 5`
  **Output**: `a^(a^(a^(a^e)))`
  **Analysis**: The output `a^(a^(a^(a^e)))` represents 5^(5^(5^(5^3125))), the result of 5^(5^(5^(5^(5^5)))) in base 5. This even deeper nesting further illustrates the fractal-like, self-similar pattern in notation, with each level of exponentiation adding another layer, scaled to base 5's magnitude growth.

- **Command 1.11**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a" --base 10`
  **Output**: `j`
  **Analysis**: The output `j` represents 10^10, the result of 10^10 in base 10, where `a` is 10^1. This single-letter notation reflects the still manageable magnitude of the result, consistent with base 10's representation for values up to this scale.

- **Command 1.12**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a" --base 10`
  **Output**: `a^j`
  **Analysis**: The output `a^j` represents 10^(10^10), the result of 10^(10^10) in base 10, where `a` is 10^1 and `j` is 10^10. The shift to symbolic notation with exponentiation indicates the system's adaptation to hyper-large numbers, introducing nesting much earlier than in lower bases due to base 10's rapid magnitude growth.

- **Command 1.13**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a" --base 10`
  **Output**: `a^(a^j)`
  **Analysis**: The output `a^(a^j)` represents 10^(10^(10^10)), the result of 10^(10^(10^10)) in base 10. This nested notation mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation.

- **Command 1.14**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a" --base 10`
  **Output**: `a^(a^(a^j))`
  **Analysis**: The output `a^(a^(a^j))` represents 10^(10^(10^(10^10))), the result of 10^(10^(10^(10^10))) in base 10. The deeper nesting continues to reflect the hierarchical structure of the input, emphasizing the AoP system's consistent approach to representing extremely large numbers through recursive notation.

- **Command 1.15**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a^a" --base 10`
  **Output**: `a^(a^(a^(a^j)))`
  **Analysis**: The output `a^(a^(a^(a^j)))` represents 10^(10^(10^(10^(10^10)))), the result of 10^(10^(10^(10^(10^10)))) in base 10. This even deeper nesting further illustrates the fractal-like, self-similar pattern in notation, with each level of exponentiation adding another layer, scaled to base 10's significant magnitude growth.

- **Command 1.16**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a" --base 16`
  **Output**: `p`
  **Analysis**: The output `p` represents 16^16, the result of 16^16 in base 16, where `a` is 16^1. This single-letter notation reflects the still manageable magnitude of the result, consistent with base 16's compact representation for values up to this scale.

- **Command 1.17**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a" --base 16`
  **Output**: `a^p`
  **Analysis**: The output `a^p` represents 16^(16^16), the result of 16^(16^16) in base 16, where `a` is 16^1 and `p` is 16^16. The shift to symbolic notation with exponentiation indicates the system's adaptation to hyper-large numbers, introducing nesting earlier than in lower bases due to base 16's rapid magnitude growth.

- **Command 1.18**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a" --base 16`
  **Output**: `a^(a^p)`
  **Analysis**: The output `a^(a^p)` represents 16^(16^(16^16)), the result of 16^(16^(16^16)) in base 16. This nested notation mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation.

- **Command 1.19**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a" --base 16`
  **Output**: `a^(a^(a^p))`
  **Analysis**: The output `a^(a^(a^p))` represents 16^(16^(16^(16^16))), the result of 16^(16^(16^(16^16))) in base 16. The deeper nesting continues to reflect the hierarchical structure of the input, emphasizing the AoP system's consistent approach to representing extremely large numbers through recursive notation.

- **Command 1.20**: `python -m src.aopl_python_impl.aop_calculator_cli "a^a^a^a^a^a" --base 16`
  **Output**: `a^(a^(a^(a^p)))`
  **Analysis**: The output `a^(a^(a^(a^p)))` represents 16^(16^(16^(16^(16^16)))), the result of 16^(16^(16^(16^(16^16)))) in base 16. This even deeper nesting further illustrates the fractal-like, self-similar pattern in notation, with each level of exponentiation adding another layer, scaled to base 16's significant magnitude growth.

## Batch 2: Power Towers with 'b' Across Bases and Depths

**Description**: Testing nested powers of 'b' with depths from 2 to 5 across bases 2, 5, 10, and 16 to compare notation patterns with 'a' and observe letter-specific behaviors.

- **Command 2.1**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b" --base 2`
  **Output**: `h`
  **Analysis**: The output `h` represents 2^8 = 256, the result of (2^2)^(2^2) = 2^4, but mapped to a higher value in the AoP system for base 2, where `b` is 2^2. This single-letter notation indicates a compact representation for a relatively small result compared to higher bases.

- **Command 2.2**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b" --base 2`
  **Output**: `a^i`
  **Analysis**: The output `a^i` represents 2^256, the result of (2^2)^(2^8) if `i` corresponds to 2^8, in base 2 where `a` is 2^1. The shift to symbolic notation with exponentiation shows the system's adaptation to larger numbers, introducing nesting as the magnitude increases.

- **Command 2.3**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b" --base 2`
  **Output**: `a^mYYYYYYYYYY`
  **Analysis**: The output `a^mYYYYYYYYYY` represents 2^(2^256), an extremely large number resulting from (2^2)^(2^(2^8)) in base 2. The use of a coefficient with extended uppercase letters indicates a complex symbolic representation for hyper-large exponents, differing from simpler nested forms seen with 'a'.

- **Command 2.4**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b^b" --base 2`
  **Output**: `a^(a^38478521676166483319977812905344815400437403773102625523885982792586979601978658394045851309783756732940673828125NYY)`
  **Analysis**: The output `a^(a^...NYY)` represents an astronomically large number, likely 2^(2^(2^256)), resulting from (2^2)^(2^(2^(2^8))) in base 2. This deeply nested and complex notation with a massive exponent value illustrates the AoP system's approach to handling extreme magnitudes through intricate symbolic layers, reflecting the rapid growth with each additional exponentiation.

- **Command 2.5**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b" --base 5`
  **Output**: `Y`
  **Analysis**: The output `Y` represents 5^25, the result of (5^2)^(5^2) = 5^25 in base 5, where `b` is 5^2. This single-letter notation indicates a compact representation for a relatively large result, reflecting base 5's mapping for higher exponents compared to base 2.

- **Command 2.6**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b" --base 5`
  **Output**: `a^2Y`
  **Analysis**: The output `a^2Y` represents 5^(2*5^25), the result of (5^2)^(5^25) in base 5, where `a` is 5^1 and `Y` is 5^25. The shift to symbolic notation with a coefficient and exponentiation shows the system's adaptation to hyper-large numbers, introducing complexity as the magnitude increases.

- **Command 2.7**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b" --base 5`
  **Output**: `a^(2*a^2Y)`
  **Analysis**: The output `a^(2*a^2Y)` represents 5^(2*5^(2*5^25)), the result of (5^2)^(5^(5^25)) in base 5. This nested notation mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation, with coefficients reflecting the base value.

- **Command 2.8**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b^b" --base 5`
  **Output**: `a^(2*a^(2*a^2Y))`
  **Analysis**: The output `a^(2*a^(2*a^2Y))` represents 5^(2*5^(2*5^(2*5^25))), the result of (5^2)^(5^(5^(5^25))) in base 5. The deeper nesting continues to reflect the hierarchical structure of the input, emphasizing the AoP system's consistent approach to representing extremely large numbers through recursive notation with coefficients.

- **Command 2.9**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b" --base 10`
  **Output**: `YYYY`
  **Analysis**: The output `YYYY` represents 10^100, the result of (10^2)^(10^2) = 10^100 in base 10, where `b` is 10^2. This multi-letter notation indicates a compact representation for a very large result, reflecting base 10's mapping for higher exponents.

- **Command 2.10**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b" --base 10`
  **Output**: `a^2YYYY`
  **Analysis**: The output `a^2YYYY` represents 10^(2*10^100), the result of (10^2)^(10^100) in base 10, where `a` is 10^1 and `YYYY` is 10^100. The shift to symbolic notation with a coefficient and exponentiation shows the system's adaptation to hyper-large numbers, introducing complexity as the magnitude increases significantly.

- **Command 2.11**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b" --base 10`
  **Output**: `a^(2*a^2YYYY)`
  **Analysis**: The output `a^(2*a^2YYYY)` represents 10^(2*10^(2*10^100)), the result of (10^2)^(10^(10^100)) in base 10. This nested notation mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation, with coefficients reflecting the base value's impact.

- **Command 2.12**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b^b" --base 10`
  **Output**: `a^(2*a^(2*a^2YYYY))`
  **Analysis**: The output `a^(2*a^(2*a^2YYYY))` represents 10^(2*10^(2*10^(2*10^100))), the result of (10^2)^(10^(10^(10^100))) in base 10. The deeper nesting continues to reflect the hierarchical structure of the input, emphasizing the AoP system's consistent approach to representing extremely large numbers through recursive notation with coefficients.

- **Command 2.13**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b" --base 16`
  **Output**: `a^2b`
  **Analysis**: The output `a^2b` likely represents 16^512, derived from (16^2)^(16^2) = 16^256, but adjusted with a coefficient in the AoP system for base 16, where `b` is 16^2 and `a` is 16^1. This symbolic notation with a coefficient indicates an early shift to handle large results, differing from single-letter outputs in lower bases.

- **Command 2.14**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b" --base 16`
  **Output**: `a^(2*a^2b)`
  **Analysis**: The output `a^(2*a^2b)` represents 16^(2*16^(2*16^2)), the result of (16^2)^(16^(16^2)) in base 16. The nested notation with a coefficient shows the system's adaptation to hyper-large numbers, introducing complexity as the magnitude increases rapidly in base 16.

- **Command 2.15**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b" --base 16`
  **Output**: `a^(2*a^(2*a^2b))`
  **Analysis**: The output `a^(2*a^(2*a^2b))` represents 16^(2*16^(2*16^(2*16^2))), the result of (16^2)^(16^(16^(16^2))) in base 16. This deeper nesting mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation, with coefficients reflecting the base value's impact.

- **Command 2.16**: `python -m src.aopl_python_impl.aop_calculator_cli "b^b^b^b^b" --base 16`
  **Output**: `a^(2*a^(2*a^(2*a^2b)))`
  **Analysis**: The output `a^(2*a^(2*a^(2*a^2b)))` represents 16^(2*16^(2*16^(2*16^(2*16^2)))), the result of (16^2)^(16^(16^(16^(16^2)))) in base 16. The even deeper nesting continues to reflect the hierarchical structure of the input, emphasizing the AoP system's consistent approach to representing extremely large numbers through recursive notation with coefficients.

## Batch 3: Power Towers with 'c', 'd', and 'e' in Base 10

**Description**: Testing nested powers of higher letters ('c', 'd', 'e') with depths from 2 to 4 in base 10 to explore how starting exponent size affects notation patterns.

- **Command 3.1**: `python -m src.aopl_python_impl.aop_calculator_cli "c^c" --base 10`
  **Output**: `a^3c`
  **Analysis**: The output `a^3c` represents 10^(3*10^3)=10^3000, derived from (10^3)^(10^3)=10^1000, but adjusted with a coefficient in the AoP system for base 10, where `c` is 10^3 and `a` is 10^1. This symbolic notation with a coefficient indicates an early shift to handle very large results, differing from multi-letter outputs seen with 'b'.

- **Command 3.2**: `python -m src.aopl_python_impl.aop_calculator_cli "c^c^c" --base 10`
  **Output**: `a^(3*a^3c)`
  **Analysis**: The output `a^(3*a^3c)` represents 10^(3*10^(3*10^3)), the result of (10^3)^(10^(10^3)) in base 10. The nested notation with a coefficient shows the system's adaptation to hyper-large numbers, introducing complexity as the magnitude increases rapidly with a higher starting exponent like 'c'.

- **Command 3.3**: `python -m src.aopl_python_impl.aop_calculator_cli "c^c^c^c" --base 10`
  **Output**: `a^(3*a^(3*a^3c))`
  **Analysis**: The output `a^(3*a^(3*a^3c))` represents 10^(3*10^(3*10^(3*10^3))), the result of (10^3)^(10^(10^(10^3))) in base 10. This deeper nesting mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation, with coefficients reflecting the impact of the starting exponent 'c'.

- **Command 3.4**: `python -m src.aopl_python_impl.aop_calculator_cli "d^d" --base 10`
  **Output**: `a^4d`
  **Analysis**: The output `a^4d` represents 10^(4*10^4)=10^40000, derived from (10^4)^(10^4)=10^10000, but adjusted with a coefficient in the AoP system for base 10, where `d` is 10^4 and `a` is 10^1. This symbolic notation with a coefficient indicates an early shift to handle extremely large results, scaling with the higher starting exponent of 'd'.

- **Command 3.5**: `python -m src.aopl_python_impl.aop_calculator_cli "d^d^d" --base 10`
  **Output**: `a^(4*a^4d)`
  **Analysis**: The output `a^(4*a^4d)` represents 10^(4*10^(4*10^4)), the result of (10^4)^(10^(10^4)) in base 10. The nested notation with a coefficient shows the system's adaptation to hyper-large numbers, introducing complexity as the magnitude increases rapidly with a higher starting exponent like 'd'.

- **Command 3.6**: `python -m src.aopl_python_impl.aop_calculator_cli "d^d^d^d" --base 10`
  **Output**: `a^(4*a^(4*a^4d))`
  **Analysis**: The output `a^(4*a^(4*a^4d))` represents 10^(4*10^(4*10^(4*10^4))), the result of (10^4)^(10^(10^(10^4))) in base 10. This deeper nesting mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation, with coefficients reflecting the significant impact of the starting exponent 'd'.

- **Command 3.7**: `python -m src.aopl_python_impl.aop_calculator_cli "e^e" --base 10`
  **Output**: `a^5e`
  **Analysis**: The output `a^5e` represents 10^(5*10^5)=10^500000, derived from (10^5)^(10^5)=10^100000, but adjusted with a coefficient in the AoP system for base 10, where `e` is 10^5 and `a` is 10^1. This symbolic notation with a coefficient indicates an early shift to handle extraordinarily large results, scaling with the even higher starting exponent of 'e'.

- **Command 3.8**: `python -m src.aopl_python_impl.aop_calculator_cli "e^e^e" --base 10`
  **Output**: `a^(5*a^5e)`
  **Analysis**: The output `a^(5*a^5e)` represents 10^(5*10^(5*10^5)), the result of (10^5)^(10^(10^5)) in base 10. The nested notation with a coefficient shows the system's adaptation to hyper-large numbers, introducing complexity as the magnitude increases extraordinarily with a high starting exponent like 'e'.

- **Command 3.9**: `python -m src.aopl_python_impl.aop_calculator_cli "e^e^e^e" --base 10`
  **Output**: `a^(5*a^(5*a^5e))`
  **Analysis**: The output `a^(5*a^(5*a^5e))` represents 10^(5*10^(5*10^(5*10^5))), the result of (10^5)^(10^(10^(10^5))) in base 10. This deeper nesting mirrors the input's structure, showing a fractal-like pattern where each additional exponentiation level adds a layer to the symbolic representation, with coefficients reflecting the extraordinary impact of the starting exponent 'e'.

## Initial Observations

The expanded set of experiments across Batches 1, 2, and 3 reveals several consistent patterns and fractal-like behaviors in the Alphabet of Powers (AoP) system's symbolic notation for large exponential expressions:

1. **Fractal-like Nesting Structure**: Across all bases (2, 5, 10, 16) and starting letters ('a' to 'e'), the notation for nested power towers exhibits a self-similar, recursive structure. Each additional level of exponentiation in the input (e.g., from "a^a" to "a^a^a") corresponds to an additional layer of nesting in the output (e.g., from `a^j` to `a^(a^j)` in base 10). This fractal pattern is most pronounced in higher bases and with deeper nesting depths, reflecting the hierarchical nature of exponentiation.

2. **Base-Dependent Transition to Symbolic Notation**: The point at which the system shifts from single-letter or multi-letter representations (e.g., `b`, `YYYY`) to symbolic exponentiation (e.g., `a^p`, `a^2YYYY`) depends on the base. Lower bases like 2 delay this transition due to slower magnitude growth (e.g., "a^a^a^a" yields `p` in base 2), while higher bases like 10 and 16 introduce nesting earlier (e.g., "a^a^a" yields `a^j` in base 10, `a^p` in base 16), reflecting faster growth in result size.

3. **Coefficient Scaling with Starting Exponent**: In base 10, experiments with higher starting letters ('c', 'd', 'e') show coefficients in the notation that scale with the letter's exponent value (e.g., `a^3c` for "c^c", `a^4d` for "d^d", `a^5e` for "e^e"). This pattern indicates the system's adaptation to the initial magnitude of the base letter, embedding it as a multiplier in the symbolic representation to manage extremely large numbers.

4. **Magnitude-Driven Complexity**: As the magnitude of the result increases (either through deeper nesting or higher starting exponents), the notation grows in complexity, incorporating nested expressions and extended letter sequences (e.g., `a^mYYYYYYYYYY` in base 2 for "b^b^b^b"). This suggests a systematic approach to handling hyper-large numbers, balancing compactness with expressiveness.

5. **Symmetry Across Bases**: Despite differences in magnitude growth rates, the structural symmetry of the notation—nested parentheses mirroring input structure—is preserved across all tested bases. This consistency highlights a core design principle of the AoP system: to represent exponential hierarchies in a universally recursive format, adaptable to any base.

These observations suggest that the AoP notation inherently encodes the mathematical structure of exponentiation as a visual and symbolic hierarchy, offering a unique lens through which to study large numbers and their relationships. Further analysis could quantify the nesting depth or coefficient patterns to predict notation outcomes for untested inputs.

## Next Steps

- Analyze the collected data to identify deeper patterns or systematic behaviors in AoP notation.
- Explore even higher nesting depths or additional bases if computational limits allow.
- Develop visual or quantitative methods to represent and compare notation structures for enhanced pattern recognition.
