# aop_parser.py

Implements the expression parser using Pratt parsing technique.

## Key Components

### Token Types

- `LETTER`: a-z, A-Z
- `WORD`: Sequence of letters
- `NUMBER`: Integers, floats, scientific notation
- `CONSTANT`: #pi, #e, #phi
- `OPERATOR`: +, -, *, /, ^
- `FUNCTION`: sqrt, log, sin, etc.

### Parser Class

#### Methods

- `parse(self)`: Main parsing entry point
- `parse_expression(self, rbp=0)`: Parse expressions with right binding power
- `parse_prefix(self)`: Handle prefix tokens
- `parse_infix(self, left)`: Handle infix tokens

### Token Handling

- `_parse_identifier()`: Handle variables and functions
- `_parse_number()`: Parse numeric literals
- `_parse_string()`: Handle quoted strings

## Pratt Parsing

Uces binding power values:

- `+`, `-`: 10
- `*`, `/`: 20
- `^`: 30 (right-associative)
- Function calls: 40

## AST Nodes

- `BinaryOpNode`: Left, operator, right
- `UnaryOpNode`: Operator, operand
- `FunctionNode`: Function name, arguments
- `VariableNode`: Variable name
- `ConstantNode`: Constant value
- `LiteralNode`: Numeric or string value

## Example

```python
from aopl_python_impl.aop_parser import Parser

parser = Parser("sqrt(a) + 2*b")
ast = parser.parse()
# AST:
#   BinaryOpNode('+',
#     FunctionNode('sqrt', [VariableNode('a')]),
#     BinaryOpNode('*',
#       LiteralNode(2),
#       VariableNode('b')
#     )
#   )
