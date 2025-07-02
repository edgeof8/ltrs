# aopl_python_impl/aop_ast.py
from abc import ABC, abstractmethod
from typing import Any
from .definitions import Token

class ASTNode(ABC):
    @abstractmethod
    def __repr__(self) -> str: pass
    @abstractmethod
    def to_str(self) -> str: pass

class NumberNode(ASTNode):
    def __init__(self, token: Token): self.token = token; self.value = token.value
    def __repr__(self) -> str: return f"Number({self.value})"
    def to_str(self) -> str: return str(self.value)

class IdentifierNode(ASTNode):
    def __init__(self, token: Token): self.token = token; self.name = token.value
    def __repr__(self) -> str: return f"Identifier({self.name})"
    def to_str(self) -> str: return self.name

class AopLiteralNode(ASTNode):
    def __init__(self, token: Token): self.token = token; self.value = token.value
    def __repr__(self) -> str: return f"AopLiteral({self.value})"
    def to_str(self) -> str: return self.value

class BinaryOpNode(ASTNode):
    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        self.left = left; self.op = op; self.right = right
    def __repr__(self) -> str: return f"BinaryOp({repr(self.left)}, {self.op.value}, {repr(self.right)})"
    def to_str(self) -> str: return f"({self.left.to_str()} {self.op.value} {self.right.to_str()})"

class UnaryOpNode(ASTNode):
    def __init__(self, op: Token, right: ASTNode): self.op = op; self.right = right
    def __repr__(self) -> str: return f"UnaryOp({self.op.value}, {repr(self.right)})"
    def to_str(self) -> str: return f"({self.op.value}{self.right.to_str()})"

class SymbolicPowerNode(ASTNode):
    def __init__(self, base: Any, exponent: Any): self.base = base; self.exponent = exponent
    def __repr__(self) -> str: return f"SymbolicPower({repr(self.base)}, {repr(self.exponent)})"
    def to_str(self) -> str: return f"({self.base.to_str()}^{self.exponent.to_str()})"
