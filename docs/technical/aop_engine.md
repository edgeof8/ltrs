# aop_engine.py

Implements the core evaluation engine for Alphabet of Powers expressions.

## Key Components

### `AoPEngine`

Main class that handles expression evaluation using Pratt parsing.

#### Key Methods

- `evaluate(expression: str)`: Parse and evaluate expression
- `_parse_expression(rbp=0)`: Parse with right binding power
- `_parse_prefix()`: Handle prefix tokens
- `_parse_infix(left)`: Handle infix tokens

### Evaluation Workflow

1. Tokenize input expression
2. Build abstract syntax tree (AST)
3. Recursively evaluate nodes:
   - Apply operations based on node type
   - Handle variables and functions
4. Return simplified result

### Special Handling

- Variable assignment: `=` operator
- Function calls: `sqrt()`, `log()`, etc.
- Constant values: `#pi`, `#e`
- Complex numbers: `(3+4j)`

## Example Usage

```python
from aopl_python_impl.aop_engine import AoPEngine

engine = AoPEngine(base=10)
result = engine.evaluate("j^j^j")
print(result)  # a^a^u
