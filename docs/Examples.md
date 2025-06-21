# AoP Suite Examples

Explore practical usage of the AoP Suite through these examples. All examples use base 10 unless specified.

## 1. CLI Examples

### Basic Operations

```bash
# Multiplication
ltrs "c*a*t"     # → x (10^24)

# Division
ltrs "x / a"     # → w (10^23)

# Exponentiation with Z
ltrs "Z^2"       # → a^200 (10^200)
```

### Hyper-Operations

```bash
# Tetration (right-associative)
ltrs "j^j"       # → a^k (10^(10^10))

# Using Z in expressions
ltrs "a^Z"       # → 10^100 → Z (direct match formatting)
ltrs "2*Z"       # → 2*10^100 → 2Z (coefficient-letter format)

# Nested operations
ltrs "b^b^b"     # → a^(2Z^2) (squashed format)
```

### Mathematical Functions

```bash
# Constants with Z
ltrs "#e * Z"    # → 2.71828 * 10^100

# Logarithms
ltrs "log(Z)"    # → 100

# Complex numbers
ltrs "sqrt(-Z)"  # → 0 + 10^50j
```

## 2. Cosmic Scratchpad GUI Examples

### Node-Based Calculations

```
// Create calculation nodes
$radius = 2.5b
$pi = #pi
$area = $pi * $radius^2

// Dependent node
$circumference = 2 * $pi * $radius
```

### Slash Commands

```
// Show variables
/vars

// Explain last calculation
/explain last

// Change base to 2
/setbase 2

// List constants
/constants
```

### Drawing Tools

1. Create calculation nodes for circle properties
2. Use line tool to connect radius → area → circumference
3. Add text annotation: "Circle Properties"
4. Use pen tool to highlight key results

## 3. Advanced Applications

### Financial Modeling

```bash
# Compound interest with large values
principal = 1.5Z          # $1.5 * 10^100
rate = 0.03               # 3% annual
years = 100
future_value = principal * (1 + rate)^years
```

### Scientific Computing

```bash
# Energy-mass equivalence
mass = 1.5a               # 15 kg
c_squared = (3a)^2        # (3*10^1)^2 = 900
energy = mass * c_squared # 13.5 kJ
```

### CPU Simulation

```python
from src.aopl_python_impl.cpu_sim.hardware import CPU

cpu = CPU()
n1 = 2**1000
n2 = 2**1000 + 1

# Compare multiplication algorithms
results = cpu.benchmark_operations({
    'karatsuba': cpu.multiply_karatsuba,
    'aop_optimized': cpu.multiply_aop_optimized
}, n1, n2)
```

## 4. AI-Powered Explanations

```
/explain "a^Z + Z"
/* Output:
1. a^Z represents 10^100 (same as Z)
2. Z + Z = 2Z
3. Result: 2 * 10^100 → 2Z
*/

/explain "sqrt(-1)"
/* Output:
The square root of -1 is the imaginary unit 'j'
*/
```

For more practical applications, explore the project's `research/` directory.
