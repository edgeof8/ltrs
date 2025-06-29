# aopl_python_impl/aop_ast.py
from __future__ import annotations
from .definitions import Token

class ASTNode:
    def to_str(self) -> str:
        raise NotImplementedError

class NumberNode(ASTNode):
    def __init__(self, token: Token): self.token = token; self.value = token.value
    def __repr__(self) -> str: return f"Number({self.value})"
    def to_str(self) -> str: return self.value

class IdentifierNode(ASTNode):
    def __init__(self, token: Token): self.token = token; self.name = token.value
    def __repr__(self) -> str: return f"Identifier({self.name})"
    def to_str(self) -> str: return self.name

class BinaryOpNode(ASTNode):
    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        self.left = left; self.op = op; self.right = right
    def __repr__(self) -> str: return f"({self.left!r} {self.op.value} {self.right!r})"
    def to_str(self) -> str:
        # Handle implicit multiplication where op token is not a simple character
        op_str = self.op.value if self.op.kind != 'IMPLICIT_OPERATOR' else ''
        # Add parentheses for clarity if needed, though parser handles precedence
        return f"{self.left.to_str()}{op_str}{self.right.to_str()}"

class UnaryOpNode(ASTNode):
    def __init__(self, op: Token, right: ASTNode):
        self.op = op; self.right = right
    def __repr__(self) -> str: return f"({self.op.value}{self.right!r})"
    def to_str(self) -> str:
        return f"{self.op.value}{self.right.to_str()}"

class SymbolicPowerNode(ASTNode):
    def __init__(self, base, exponent):
        self.base = base
        self.exponent = exponent
    def __repr__(self) -> str:
        return f"SymbolicPower({self.base!r} ^ {self.exponent!r})"
    def to_str(self) -> str:
        return f"({self.base.to_str()})^{self.exponent.to_str()}"
