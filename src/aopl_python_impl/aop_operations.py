# aopl_python_impl/aop_operations.py
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode, AopLiteralNode
from .definitions import LETTER_TO_EXPONENT_MAP, AoPError, SymbolicPowerResult, Token
from .aop_value import AoPValue
import logging, pickle, base64, re
from .aop_logger import log_eval, Colors, log_pow

_eval_depth = 0

def _resolve_to_value(obj):
    # ... (this function is now correct) ...
    current = obj
    while isinstance(current, SymbolicPowerResult):
        log_pow(f"Resolving SymbolicPower: {current!r}")
        base = _resolve_to_value(current.base)
        exponent = _resolve_to_value(current.exponent)
        if isinstance(base, SymbolicPowerResult) or isinstance(exponent, SymbolicPowerResult):
             return SymbolicPowerResult(base, exponent)
        try:
            current = base ** exponent
        except Exception as e:
            if type(e).__name__ == 'PyNotImplementedError':
                log_pow(f"Power op is unresolvable. Returning symbolic: {current!r}")
                return current
            raise e
    return current

def evaluate_ast(node: ASTNode, base: int, cache: dict | None = None) -> 'AoPValue | SymbolicPowerResult':
    global _eval_depth
    node_repr = repr(node)
    base_str = str(base)
    if cache and base_str in cache and node_repr in cache[base_str]:
        cached_data = cache[base_str][node_repr]
        if "raw_pickle" in cached_data: return pickle.loads(base64.b64decode(cached_data["raw_pickle"]))

    result: 'AoPValue | SymbolicPowerResult'

    if isinstance(node, AopLiteralNode):
        # --- NEW LOGIC FOR AOP_LITERAL ---
        # It represents a single number, not a sum.
        # e.g., "5e3b" -> 5*10^5 + 3*10^2
        poly = {}
        # This regex finds terms like "5e" or "b"
        term_pattern = re.compile(r'(\d*)?([a-zA-Z])')

        # Keep track of what part of the string we've processed
        processed_value = node.value
        for match in term_pattern.finditer(node.value):
            coeff_str, letter = match.groups()
            coeff = int(coeff_str) if coeff_str else 1
            exp = LETTER_TO_EXPONENT_MAP.get(letter, 0)
            poly[str(exp)] = poly.get(str(exp), 0) + coeff
            # Remove the matched part from our tracking string
            processed_value = processed_value.replace(match.group(0), '', 1)

        # Any part of the string left must be a number (constant term)
        if processed_value.strip().isnumeric():
            poly['0'] = poly.get('0', 0) + int(processed_value.strip())

        result = AoPValue(poly=poly, base=base)
    elif isinstance(node, UnaryOpNode):
        operand = _resolve_to_value(evaluate_ast(node.right, base, cache))
        if node.op.value == '-':
            result = operand * AoPValue.from_number(-1, base=base)
        else:
            result = operand
    elif isinstance(node, BinaryOpNode):
        left = evaluate_ast(node.left, base, cache)
        right = evaluate_ast(node.right, base, cache)
        op = node.op.value
        log_eval(f"Evaluating: {left!r} {op} {right!r}", _eval_depth)

        if op in ('^', '**'):
            # Must resolve operands before creating symbolic power
            left_aop = _resolve_to_value(left)
            right_aop = _resolve_to_value(right)
            result = SymbolicPowerResult(left_aop, right_aop)
        else:
            left_aop = _resolve_to_value(left)
            right_aop = _resolve_to_value(right)
            if not isinstance(left_aop, AoPValue) or not isinstance(right_aop, AoPValue):
                raise TypeError(f"Cannot perform '{op}' on unresolved symbolic values: {left_aop!r}, {right_aop!r}")
            if op == '+': result = left_aop + right_aop
            elif op == '-': result = left_aop - right_aop
            elif op == '*': result = left_aop * right_aop
            elif op == '/': result = AoPValue.from_number(left_aop.to_numerical() // right_aop.to_numerical(), base=base)
            else: raise ValueError(f"Unknown operator: {op}")
    else:
        raise TypeError(f"Unknown AST node type: {type(node)}")

    log_eval(f"Result of '{node!r}' is {result!r}", _eval_depth)
    if cache is not None:
        if base_str not in cache: cache[base_str] = {}
        pickled_obj = pickle.dumps(result)
        b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
        cache[base_str][node_repr] = {"raw_pickle": b64_pickle}

    return result
