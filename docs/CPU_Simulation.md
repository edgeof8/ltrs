# CPU Arithmetic Simulation

This document details the CPU arithmetic simulation module in `src/aopl_python_impl/cpu_sim/hardware.py`, which benchmarks multiplication algorithms for large numbers.

## Introduction

The CPU simulation module:

- Implements and tests multiplication algorithms
- Features an intelligent dispatcher that selects optimal algorithms
- Compares performance characteristics in Python
- Helps understand how algorithm choice impacts complex calculations

**Note**: Results are specific to Python and may differ from low-level implementations.

## Core CPU Class

### Initialization

```python
def __init__(self):
    # Constants for dispatch logic
    self.KARATSUBA_THRESHOLD_BITS = 1024  # Use Karatsuba above this
    self.DENSE_THRESHOLD_FACTOR = 0.9     # 90% bits set = dense
    self.SPARSE_POPCOUNT_THRESHOLD = 2     # Max set bits for "very sparse"

    # Lookup table for small numbers
    self.LUT_CHUNK极
```

[Response interrupted by a tool use result. Only one tool may be used at a time and should be placed at the end of the message.]
