# aopl_python_impl/aop_ast.py
from __future__ import annotations
from typing import Any
from .definitions import Token

class ASTNode:
    def to_str(self) -> str:
        raise NotImplementedError

class NumberNode(ASTNode):
    def __init__(self, token: Token):
        self.token = token
        self.value = token.value
    def __repr__(self) -> str: return f"Number({self.value})"
    def to_str(self) -> str: return str(self.value) if self.value is not None else ""

class IdentifierNode(ASTNode):
    def __init__(self, token: Token):
        self.token = token
        self.name = token.value
    def __repr__(self) -> str: return f"Identifier({self.name})"
    def to_str(self) -> str: return self.name if self.name is not None else ""

class AopLiteralNode(ASTNode):
    def __init__(self, token: Token):
        self.token = token
        self.value = token.value
    def __repr__(self) -> str: return f"AopLiteral({self.value})"
    def to_str(self) -> str: return self.value if self.value is not None else ""

class BinaryOpNode(ASTNode):
    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        self.left = left; self.op = op; self.right = right
    def __repr__(self) -> str: return f"BinaryOp({self.left!r}, '{self.op.value}', {self.right!r})"
    def to_str(self) -> str:
        return f"({self.left.to_str()} {self.op.value} {self.right.to_str()})"

class UnaryOpNode(ASTNode):
    def __init__(self, op: Token, right: ASTNode):
        self.op = op; self.right = right
    def __repr__(self) -> str: return f"UnaryOp('{self.op.value}', {self.right!r})"
    def to_str(self) -> str:
        return f"({self.op.value}{self.right.to_str()})"

class SymbolicPowerNode(ASTNode):
    def __init__(self, base: Any, exponent: Any):
        self.base = base
        self.exponent = exponent
    def __repr__(self) -> str:
        return f"SymbolicPower({self.base!r} ^ {self.exponent!r})"
    def to_str(self) -> str:
        return f"({self.base.to_str()})^{self.exponent.to_str()}"
