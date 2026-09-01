# aopl_python_impl/aop_operations.py
#
# This module contains the core recursive function, `evaluate_ast`, which
# walks the Abstract Syntax Tree and performs the actual calculations.
# It handles operator logic, variable lookups/assignments, and caching of
# sub-expression results.
from typing import Dict, Any, Union, Optional
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode, AopLiteralNode, VariableNode
from .definitions import AoPError, SymbolicPowerResult
from .aop_value import AoPValue
from .aop_logger import log_eval, log_pow

_eval_depth = 0

def _resolve_to_value(current: Union[AoPValue, SymbolicPowerResult]) -> Union[AoPValue, SymbolicPowerResult]:
    """
    Recursively resolves a potentially nested SymbolicPowerResult.
    This is the "lazy evaluation" engine, turning symbolic powers into concrete AoPValues.
    """
    while isinstance(current, SymbolicPowerResult):
        log_pow(f"Resolving SymbolicPower: {current!r}", _eval_depth)
        base = _resolve_to_value(current.base)
        exponent = _resolve_to_value(current.exponent)
        if isinstance(base, SymbolicPowerResult) or isinstance(exponent, SymbolicPowerResult):
            return SymbolicPowerResult(base, exponent)
        # Perform the power operation
        result_aop = base ** exponent
        # The result of the power op could itself be another symbolic power if the exponent
        # was symbolic (e.g. (a^b)^c -> a^(b*c)). The loop continues until a final value is reached.
        current = result_aop

    return current

def evaluate_ast(node: ASTNode, base: int, cache: Optional[dict] = None, variables: Optional[Dict[str, Any]] = None) -> Union[AoPValue, SymbolicPowerResult]:
    # `cache` is an in-memory memo for this evaluation only (live objects, never pickle).
    if variables is None:
        variables = {}
    global _eval_depth
    node_repr = repr(node)
    memo_key = (base, node_repr)
    if cache is not None and memo_key in cache:
        log_eval(f"Cache HIT for sub-expression: {node_repr}", _eval_depth)
        return cache[memo_key]

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
        elif isinstance(node, VariableNode):
            var_name = node.name
            if var_name not in variables:
                raise NameError(f"Variable '{var_name}' is not defined.")
            # The result is the value stored in the variable dictionary
            result = variables[var_name]
        elif isinstance(node, UnaryOpNode):
            operand = _resolve_to_value(evaluate_ast(node.right, base, cache, variables))
            if not isinstance(operand, AoPValue): raise TypeError(f"Cannot apply unary '{node.op.value}' to a non-numeric value")
            if node.op.value == '-':
                result = AoPValue.from_number(0, base) - operand
            else: # Unary '+'
                result = operand
        elif isinstance(node, BinaryOpNode):
            log_eval(f"Node: {node.to_str()}", _eval_depth - 1)

            op = node.op.value
            # Handle assignment separately as it has special logic
            # It modifies state (the variables dict) and has right-to-left associativity.
            if op == '=':
                if not isinstance(node.left, VariableNode):
                    raise SyntaxError("Assignment target must be a variable (e.g., $x).")
                var_name = node.left.name
                value_to_assign = evaluate_ast(node.right, base, cache, variables)
                resolved_value = _resolve_to_value(value_to_assign)
                variables[var_name] = resolved_value
                result = resolved_value # Assignment expressions return the assigned value
            else:
                left = evaluate_ast(node.left, base, cache, variables)
                right = evaluate_ast(node.right, base, cache, variables)
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
                        try:
                            result = left_aop / right_aop
                        except ValueError as e:
                            raise AoPError(str(e)) from e
                    elif op == '==':
                        # Compare numerical values for equality, return 1 or 0
                        is_equal = left_aop.to_numerical() == right_aop.to_numerical()
                        result = AoPValue.from_number(1 if is_equal else 0, base)
                    else:
                        raise AoPError(f"Unsupported operator: {op}")
            log_eval(f"Result -> {result!r}", _eval_depth - 1)
        else:
            raise AoPError(f"Unknown node type: {type(node).__name__}")
        if cache is not None and not isinstance(node, VariableNode):
            cache[memo_key] = result
            log_eval(f"Cached result for: {node_repr}", _eval_depth - 1)
        return result
    finally:
        _eval_depth -= 1
