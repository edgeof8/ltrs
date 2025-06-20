# EDGE CASE EXPLORATION TEMPLATE

## Objective

Investigate boundary conditions and failure modes in symbolic pattern generation.

## Focus Areas

1. **Base Transition Points**: Behavior near base=1.0
2. **Depth-Induced Pattern Collapse**: Critical nesting levels
3. **Extreme Coefficients**: Very large/small multipliers
4. **Mixed Base Expressions**: Cross-base operations

## Procedure

### 1. Base Transition Analysis

```bash
# Test bases near 1.0
for base in 0.9 0.99 1.0 1.01 1.1; do
  python -m src.aopl_python_impl.aop_calculator_cli "a^a^a" --base $base
done
```

### 2. Depth Limit Testing

```python
# Test increasing depths until failure
depth = 3
while True:
    expr = 'a' + '^a' * depth
    result = run_cli(expr, base=10)
    if "Error" in result:
        log_failure(depth, expr)
        break
    depth += 1
```

### 3. Extreme Coefficient Handling

```bash
# Large coefficients
python -m src.aopl_python_impl.aop_calculator_cli "1000000000000000a" --base 10

# Small coefficients
python -m src.aopl_python_impl.aop_calculator_cli "0.000000000000001a" --base 10
```

## Documentation Protocol

1. Record exact input parameters
2. Capture full CLI output
3. Classify failure modes:
   - Overflow
   - Underflow
   - Recursion depth
   - Pattern degradation
4. Note any unexpected pattern behaviors

## Analysis Framework

```mermaid
graph TD
    A[Edge Case] --> B[Reproduce]
    B --> C[Document Behavior]
    C --> D[Classify Failure]
    D --> E[Propose Solution]
    E --> F[Update System Rules]
