# CPU Arithmetic Simulation

This document details the CPU arithmetic simulation component found within the `ltrs` project, specifically in the `src.aopl_python_impl.cpu_sim.hardware` module.

## Introduction

The primary purpose of this simulation is to explore and benchmark different low-level integer arithmetic operations, particularly multiplication. It provides a platform to:

- Implement and test various multiplication algorithms.
- Develop an "intelligent" dispatcher that selects the most appropriate algorithm based on input characteristics.
- Compare their performance characteristics within a Python environment.
- Understand how the choice of a fundamental algorithm can impact the performance of more complex calculations.

**Disclaimer:** This is a Python-based simulation. The performance results observed here are specific to this environment (Python's list manipulations, function call overhead, etc.) and may differ significantly from actual hardware implementations or highly optimized low-level language implementations of these algorithms.

## Core `CPU` Class

All simulated multiplication algorithms are encapsulated within a `CPU` class defined in `hardware.py`. This class also houses the `intelligent_multiply` method.

### `CPU.__init__(self)`

- Initializes constants used for dispatch logic:
  - `KARATSUBA_THRESHOLD_BITS`: Bit length above which Karatsuba is generally preferred for large numbers (e.g., 1024).
  - `DENSE_THRESHOLD_FACTOR`: Factor to determine if a number is "dense" (e.g., 0.9, meaning 90% of bits are set).
  - `SPARSE_POPCOUNT_THRESHOLD`: Maximum number of set bits for a number to be considered "very sparse" (e.g., 2).
- Initializes and precomputes a lookup table for small multiplications:
  - `LUT_CHUNK_SIZE`: Defines the bit size of numbers for direct lookup (e.g., 8, meaning 0-255).
  - `self.lookup_table`: A dictionary storing `(i, j) -> i*j` for all numbers up to `(1 << LUT_CHUNK_SIZE) - 1`.

### `CPU.intelligent_multiply(self, n1: int, n2: int) -> int`

This is the central method that analyzes `n1` and `n2` and dispatches to one of the private multiplication methods. The dispatch logic is as follows (in order of precedence):

1.  **Direct LUT Lookup**: If both `n1` and `n2` are smaller than `(1 << LUT_CHUNK_SIZE)` (e.g., < 256), their product is returned directly from `self.lookup_table`.
2.  **Karatsuba's Domain**: If the maximum bit length of `n1` or `n2` exceeds `KARATSUBA_THRESHOLD_BITS`, `_multiply_karatsuba` is used.
3.  **Schoolbook's Niche**: If one number is "dense" (popcount > bit_length \* `DENSE_THRESHOLD_FACTOR`) AND the other is "very sparse" (popcount <= `SPARSE_POPCOUNT_THRESHOLD`), `_multiply_schoolbook` is used.
4.  **AoP's Niche (Sparse \* Sparse)**: If BOTH numbers are "very sparse", `_multiply_aop_optimized` is used.
5.  **Default (AoP Optimized)**: For all other cases (typically general-purpose numbers up to `KARATSUBA_THRESHOLD_BITS`), `_multiply_aop_optimized` is used, as it has shown strong performance in simulation for these ranges.

## Simulated Hardware Primitives

The simulation is built upon a few core "hardware" primitives that operate on numbers represented as lists of bits (LSB first):

- **`number_to_bitlist(n: int) -> List[int]`**: Converts an integer to its bit-list representation.
- **`bitlist_to_number(bits: List[int]) -> int`**: Converts a bit-list back to an integer.
- **`_add_primitive(b1: List[int], b2: List[int]) -> List[int]`**: A general-purpose adder for two bit-lists.
- **`_subtract_primitive(b1: List[int], b2: List[int]) -> List[int]`**: Subtracts bit-list `b2` from `b1`.
- **`_shift_primitive(bits: List[int], amount: int) -> List[int]`**: Left-shifts a bit-list.
- **`_add_sparse_inplace_primitive(bits: List[int], exp: int) -> None`**: Efficiently adds `2^exp` to a bit-list in-place.

## Multiplication Algorithms Implemented (as private CPU methods)

1.  **`_multiply_schoolbook(self, n1, n2)`**: Standard iterative schoolbook method.
2.  **`_multiply_aop_optimized(self, n1, n2)`**: AoP/cross-product method, optimized with `_add_sparse_inplace_primitive`.
3.  **`_multiply_karatsuba(self, n1, n2)`**: Recursive Karatsuba algorithm.
4.  **`_multiply_lookup_table(self, n1, n2)`**:
    - Breaks `n1` and `n2` into chunks based on `self.LUT_CHUNK_SIZE`.
    - Looks up products of chunk pairs from `self.lookup_table`.
    - Shifts and sums these partial products using `_add_primitive` for a "fair" simulation against other algorithms. This method is primarily for correctness testing and academic comparison, as its simulated performance with many `_add_primitive` calls is not competitive for larger numbers against the more optimized algorithms.

## Complex Operations Implemented

Module-level functions for more complex arithmetic operations, parameterized to use any `multiply_func` (typically one of the CPU's methods):

1.  **`power_integer(base_n: int, exponent_n: int, multiply_func: callable) -> int`**: Calculates `base_n ^ exponent_n` using exponentiation by squaring.
2.  **`multiply_then_add(n1: int, n2: int, n3: int, multiply_func: callable) -> int`**: Calculates `(n1 * n2) + n3`.

## Testing (`tests/cpu_sim_tests/`)

The test suite for the CPU simulation has been refactored into multiple files within the `tests/cpu_sim_tests/` directory for better organization:

- **`test_raw_algorithms.py` (`TestRawMultiplicationAlgorithms`)**:
  - Correctness of all individual multiplication methods (Schoolbook, AoP, Karatsuba, LookupTable (chunking), Intelligent).
  - Main performance suite benchmarking Schoolbook (with cutoffs), AoP, Karatsuba, and Intelligent.
  - Specific "best-case" performance tests for Schoolbook, AoP, and Karatsuba.
- **`test_complex_operations.py` (`TestComplexOperations`)**:
  - Correctness of `power_integer` and `multiply_then_add` using all multiplication methods.
  - Performance benchmarks for these complex operations using the refined set of benchmark algorithms.
  - Includes `test_power_calculation_benchmark` for focused power calculation scenarios.
- **`test_dispatcher.py` (`TestIntelligentDispatcher`)**:
  - Correctness of the `intelligent_multiply` method's results.
  - Mock-based tests to verify the dispatch logic of `intelligent_multiply` to the correct underlying algorithms.

### Key Findings & Example Output

- **Intelligent Dispatcher**: The `intelligent_multiply` method effectively chooses the best underlying algorithm (AoP Optimized for general cases up to ~1024 bits, Karatsuba for larger, direct LUT for very small, and specific niche algorithms like Schoolbook for dense\*sparse) with negligible overhead.
- **AoP_Optimized**: Remains highly performant for a wide range of inputs in this Python simulation due to `_add_sparse_inplace_primitive`.
- **Karatsuba**: Shows its strength for very large numbers (e.g., >1024 bits).
- **LookupTable (Chunking)**: The `_multiply_lookup_table` method, when using "fair" summation with `_add_primitive`, is not performance-competitive for larger numbers against the other algorithms in this simulation. Its primary value is for correctness testing of the chunking/summation logic and for the direct small-number lookups used by `intelligent_multiply`.
- **Schoolbook**: Best in its specific dense\*sparse niche; otherwise, slower for general-purpose multiplication.

_Example Output Snippet (Main Performance Suite):_

```
Bit Length   | Runs  | Schoolbook Avg (s) | AoP_Optimized Avg (s) | Karatsuba Avg (s)  | Intelligent Avg (s)
------------------------------------------------------------------------------------------------------------
...
256          | 25    | skipped            | 0.006...           | 0.011...           | 0.006...
...
4096         | 3     | skipped            | 1.5...             | 1.0...             | 1.0...
```

### Benchmark Parameters

Run counts for performance tests are adaptive, decreasing for larger bit lengths to keep overall test suite execution time manageable. Slower algorithms like Schoolbook (and previously LookupTable chunking) are conditionally skipped in broader performance benchmarks for larger inputs.

## How to Run the Tests

To execute the full CPU simulation test suite, navigate to the project root directory and run:

```bash
python -m unittest discover tests/cpu_sim_tests
```

Or, to run a specific test file:

```bash
python -m unittest tests.cpu_sim_tests.test_raw_algorithms
```

## Interpretation of Results

The simulation provides valuable insights into algorithmic trade-offs. The `intelligent_multiply` method demonstrates a practical approach to leveraging the strengths of different algorithms. The performance of `AoP_Optimized` highlights the benefits of tailored data structures and primitives (`_add_sparse_inplace_primitive`) in a Python simulation context.
