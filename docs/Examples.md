# Alphabet of Powers (`ltrs`) Examples

Explore the capabilities of the AoP Calculator through these practical examples. All examples use base 10 unless specified.

## Basic Operations

```bash
# Multiplication
ltrs "c*a*t"     # → x (10^24)

# Division
ltrs "x / a"     # → w (10^23)

# Exponentiation
ltrs "b^3"       # → e (10^5)

# Combined operations
ltrs "2a * 5c"   # → 2*10^1 * 5*10^3 = 10^5 → e
```

## Hyper-Operations

```bash
# Simple power
ltrs "2j^2"      # → (2*10^10)^2 = 4*10^20 → 4t

# Tetration (right-associative)
ltrs "j^j"       # → a^k (10^(10^10))

# Nested tetration
ltrs "j^j^j"     # → a^a^u (10^(10^(10^10)))

# Massive number representation
ltrs "j^j^j^j"   # → a^a^a^31
```

## Mathematical Functions

```bash
# Square root
ltrs "sqrt(d)"   # → sqrt(10^4) = 10^2 → b

# Logarithms
ltrs "log(c)"    # → log10(10^3) = 3
ltrs "log2(16a)" # → log2(160) ≈ 7.3219

# Trigonometry
ltrs "sin(#pi/2)" # → 1
ltrs "cos(0)"     # → 1
ltrs "tan(#pi/4)" # → 1

# Complex numbers
ltrs "sqrt(-1)"   # → j (imaginary unit)
ltrs "(3+4j)^2"   # → (-7+24j)
```

## Working with Variables

```bash
# Assign values
radius = 2.5b      # 2.5 * 10^2 = 250
pi = #pi           # ≈ 3.14159

# Calculate area
area = pi * radius^2  # ≈ 196349.54

# Show variables
/vars
# Output:
# Variable | Value
# ---------|----------------
# area     | 196349.5408
# radius   | 2.5 * b
# pi       | 3.141592653589793

# Use in expressions
ltrs "area / 1000" # → 196.34954
```

## Graphing Capabilities

```bash
# Plot parabola
/graph x^2 for x from -5 to 5

# Exponential growth with logarithmic scale
/graph b^x for x from 0 to 3 --logy

# Sine wave with AoP constant
/graph sin(t) for t from 0 to #pi * 2

# 3D surface plot (complex numbers)
/graph real(sqrt(x + y j)) for x from -5 to 5, y from -5 to 5
```

## CPU Simulation Module

```bash
# Benchmark multiplication algorithms
from src.aopl_python_impl.cpu_sim.hardware import CPU

cpu = CPU()
n1 = 2**1000  # Very large number
n2 = 2**1000 + 1

# Intelligent algorithm selection
result = cpu.intelligent_multiply(n1, n2)

# Compare algorithms
import timeit
karatsuba_time = timeit.timeit(lambda: cpu._multiply_karatsuba(n1, n2), number=10)
aop_time = timeit.timeit(lambda: cpu._multiply_aop_optimized(n1, n2), number=10)

print(f"Karatsuba: {karatsuba_time:.6f}s")
print(f"AoP Optimized: {aop_time:.6f}s")
```

## AI-Powered Explanations

```bash
# Explain basic operation
/explain "a * b"
# Output:
# Multiplication of a (10^1) and b (10^2) results in c (10^3)
# since exponents add during multiplication: 1 + 2 = 3.

# Explain hyper-operation
/explain "j^j"
# Output:
# This represents tetration: 10^10 raised to itself (10^10)^(10^10) = 10^(10^10 * 10^10)
# which simplifies to 10^(10^11). In AoP notation, this is represented as a^k.

# Explain complex result
/explain "sqrt(-1)"
# Output:
# The square root of -1 is the imaginary unit, represented as 'j' in mathematics.
# In AoP notation, we preserve this as the complex number 0+1j.
```

## Advanced Applications

```bash
# Calculate compound interest
principal = 1000a  # $1000 * 10^1 = $10,000
rate = 0.05        # 5% annual
years = 10
future_value = principal * (1 + rate)^years

# Estimate population growth
initial_population = 7.8b  # 7.8 billion
growth_rate = 0.01         # 1% annual
years = 50
future_population = initial_population * (1 + growth_rate)^years

# Physics calculations (kinetic energy)
mass = 5c          # 5 * 10^3 kg = 5000 kg
velocity = 3a      # 3 * 10^1 m/s = 30 m/s
ke = 0.5 * mass * velocity^2
```

For more practical applications, explore the project's `notes/` directory containing advanced use cases.
