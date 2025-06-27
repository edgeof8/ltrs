# aopl_python_impl/aop_ast.py
from __future__ import annotations
from .definitions import Token

class ASTNode: pass
class NumberNode(ASTNode):
    def __init__(self, token: Token): self.token = token; self.value = token.value
    def __repr__(self) -> str: return f"Number({self.value})"
class IdentifierNode(ASTNode):
    def __init__(self, token: Token): self.token = token; self.name = token.value
    def __repr__(self) -> str: return f"Identifier({self.name})"
class BinaryOpNode(ASTNode):
    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        self.left = left; self.op = op; self.right = right
    def __repr__(self) -> str: return f"({self.left!r} {self.op.value} {self.right!r})"
class UnaryOpNode(ASTNode):
    def __init__(self, op: Token, right: ASTNode):
        self.op = op; self.right = right
    def __repr__(self) -> str: return f"({self.op.value}{self.right!r})"
