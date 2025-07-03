# aopl_python_impl/aop_operations.py
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode, AopLiteralNode
from .definitions import LETTER_TO_EXPONENT_MAP, AoPError, SymbolicPowerResult, Token
from .aop_value import AoPValue
import logging, pickle, base64, re
from .aop_logger import log_eval, Colors, log_pow

_eval_depth = 0

def _resolve_to_value(current: 'AoPValue | SymbolicPowerResult') -> 'AoPValue | SymbolicPowerResult':
    while isinstance(current, SymbolicPowerResult):
        log_pow(f"Resolving SymbolicPower: {current!r}", _eval_depth)
        base = _resolve_to_value(current.base)
        exponent = _resolve_to_value(current.exponent)
        if isinstance(base, SymbolicPowerResult) or isinstance(exponent, SymbolicPowerResult):
            return SymbolicPowerResult(base, exponent)
        # Perform the power operation
        result_aop = base ** exponent

        # CORRECTED CHECK: Call the getter directly on the returned object.
        # Ensure compatibility with Rust implementation.
        if hasattr(result_aop, 'get_coeff_as_power') and result_aop.get_coeff_as_power is not None:
            return result_aop

        current = result_aop # It's a numerical value, continue loop if needed (e.g. for (a^b)^c)

    return current

def evaluate_ast(node: ASTNode, base: int, cache: dict | None = None) -> 'AoPValue | SymbolicPowerResult':
    global _eval_depth
    # --- NEW: Sub-expression cache check ---
    # We create a unique key for each node in the AST.
    node_repr = repr(node)
    base_str = str(base)
    if cache and base_str in cache and node_repr in cache[base_str]:
        cached_data = cache[base_str][node_repr]
        if "raw_pickle" in cached_data:
            log_eval(f"Cache HIT for sub-expression: {node_repr}", _eval_depth)
            return pickle.loads(base64.b64decode(cached_data["raw_pickle"]))

    log_eval(f"Node: {node!r}", _eval_depth)
    _eval_depth += 1
    try:
        if isinstance(node, NumberNode):
            result = AoPValue.from_number(int(node.value), base)
        elif isinstance(node, IdentifierNode):
            # An identifier is a simple literal like 'a' or 'Z'
            result = AoPValue.from_literal(node.name, base)
        elif isinstance(node, AopLiteralNode):
            result = AoPValue.from_literal(node.value, base)
        elif isinstance(node, UnaryOpNode):
            operand = _resolve_to_value(evaluate_ast(node.right, base, cache))
            if not isinstance(operand, AoPValue): raise TypeError(f"Cannot apply unary '{node.op.value}' to a non-numeric value")
            if node.op.value == '-':
                result = AoPValue.from_number(0, base) - operand
            else: # Unary '+'
                result = operand
        elif isinstance(node, BinaryOpNode):
            # --- This is the type guard for Pylance ---
            # It confirms to the static analyzer that 'node' is a BinaryOpNode here.
            if not isinstance(node, BinaryOpNode):
                # This branch is logically unreachable but satisfies the type checker.
                raise AoPError("Internal error: Node type mismatch.")

            log_eval(f"Node: {node.to_str()}", _eval_depth - 1)

            left = evaluate_ast(node.left, base, cache)
            right = evaluate_ast(node.right, base, cache)
            op = node.op.value
            if op in ('^', '**'):
                # Power operation is lazy, it does not resolve its operands here
                result = SymbolicPowerResult(left, right)
            else:
                left_aop = _resolve_to_value(left)
                if not isinstance(left_aop, AoPValue): raise TypeError(f"Left operand for '{op}' could not be resolved to a value: {left_aop!r}")
                right_aop = _resolve_to_value(right)
                if not isinstance(right_aop, AoPValue): raise TypeError(f"Right operand for '{op}' could not be resolved to a value: {right_aop!r}")
                if op == '+': result = left_aop + right_aop
                elif op == '-': result = left_aop - right_aop
                elif op == '*': result = left_aop * right_aop
                elif op == '/':
                    if right_aop.to_numerical() == 0:
                        raise AoPError("Division by zero")
                    result = AoPValue.from_number(left_aop.to_numerical() // right_aop.to_numerical(), base)
                else:
                    raise AoPError(f"Unsupported operator: {op}")
            log_eval(f"Result -> {result!r}", _eval_depth - 1)
        else:
            raise AoPError(f"Unknown node type: {type(node).__name__}")
        # --- NEW: Update sub-expression cache ---
        if cache is not None:
            if base_str not in cache: cache[base_str] = {}
            # We only need to store the raw object for sub-expressions
            pickled_obj = pickle.dumps(result)
            b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
            cache[base_str][node_repr] = {"raw_pickle": b64_pickle}
            log_eval(f"Cached result for: {node_repr}", _eval_depth - 1)
        return result
    finally:
        _eval_depth -= 1
