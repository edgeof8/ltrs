# aopl_python_impl/aop_operations.py
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode
from .definitions import LETTER_TO_EXPONENT_MAP
from .aop_value import AoPValue
import logging

def evaluate_ast(node: ASTNode, base: int) -> AoPValue:
    """
    Evaluates the AST, returning an AoPValue object that represents the result
    as a polynomial. This avoids creating huge integers until the final formatting step.
    """
    if isinstance(node, NumberNode):
        # A number is a polynomial with one term: coeff * base^0
        val = AoPValue({0: int(node.value)}, base=base)
        logging.debug(f"Eval NumberNode({node.value}) -> {val!r}")
        return val
    if isinstance(node, IdentifierNode):
        # An identifier like 'b' is a polynomial for 1 * base^2
        exp = sum(LETTER_TO_EXPONENT_MAP.get(char, 0) for char in node.name)
        # This is represented as one term with a coefficient of 1.
        val = AoPValue({exp: 1}, base=base)
        logging.debug(f"Eval IdentifierNode({node.name}) -> {val!r}")
        return val
    if isinstance(node, UnaryOpNode):
        right = evaluate_ast(node.right, base)
        logging.debug(f"Eval UnaryOp({node.op.value}) on {right!r}")
        if node.op.value == '-':
            result = right * AoPValue({0: -1}, base=base)
            logging.debug(f"Unary '-' result -> {result!r}")
            return result
        return right
    if isinstance(node, BinaryOpNode):
        left = evaluate_ast(node.left, base)
        right = evaluate_ast(node.right, base)
        op = node.op.value
        logging.debug(f"Eval BinaryOp: {left!r} {op} {right!r}")
        result = None
        if op == '+': result = left + right
        if op == '-': result = left - right
        if op == '*': result = left * right
        if op == '/':
            # Division is tricky with polynomials. We'll convert to numerical and back.
            result = AoPValue({0: left.to_numerical() // right.to_numerical()}, base=base)
        if op in ('^', '**'):
            result = left ** right

        if result is not None:
            logging.debug(f"Op '{op}' result -> {result!r}")
            return result
    raise TypeError(f"Unknown AST node type: {type(node)}")
