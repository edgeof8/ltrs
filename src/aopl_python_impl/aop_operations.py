# aopl_python_impl/aop_operations.py
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode
from .definitions import LETTER_TO_EXPONENT_MAP
from .aop_value import AoPValue
import logging
# --- NEW: Imports for pickling and encoding ---
import pickle
import base64
from .aop_logger import log_eval, Colors

_eval_depth = 0

def evaluate_ast(node: ASTNode, base: int, cache: dict | None = None) -> AoPValue:
    """
    Evaluates the AST, returning an AoPValue object.
    Checks a pre-calculation cache for sub-expressions to accelerate computation.
    """
    global _eval_depth

    # --- MODIFIED: New, efficient sub-expression cache check ---
    node_str = node.to_str()
    base_str = str(base)
    if cache and base_str in cache and node_str in cache[base_str]:
        cached_data = cache[base_str][node_str]
        if "raw_pickle" in cached_data:
            logging.debug(f"Sub-expression cache hit for '{node_str}'. Unpickling.")
            pickle_data = base64.b64decode(cached_data["raw_pickle"])
            # Directly return the unpickled AoPValue object, skipping all evaluation.
            return pickle.loads(pickle_data)

    # --- If not in cache, proceed with normal evaluation ---
    # The result of the evaluation will be stored in 'result'
    result: AoPValue | None = None

    if isinstance(node, NumberNode):
        val = AoPValue.from_number(int(node.value), base=base)
        log_eval(f"Interpreted number {Colors.WHITE}'{node.value}'{Colors.ENDC} -> {Colors.BLUE}{val!r}{Colors.ENDC}", _eval_depth)
        result = val
    elif isinstance(node, IdentifierNode):
        exp = sum(LETTER_TO_EXPONENT_MAP.get(char, 0) for char in node.name)
        val = AoPValue({exp: 1}, base=base)
        log_eval(f"Interpreted identifier {Colors.WHITE}'{node.name}'{Colors.ENDC} (base^{exp}) -> {Colors.BLUE}{val!r}{Colors.ENDC} (value: {val.to_numerical()})", _eval_depth)
        result = val
    elif isinstance(node, UnaryOpNode):
        _eval_depth += 1
        right = evaluate_ast(node.right, base, cache)
        _eval_depth -= 1
        if node.op.value == '-':
            result = right * AoPValue({0: -1}, base=base)
        else: # Unary '+'
            result = right
    elif isinstance(node, BinaryOpNode):
        _eval_depth += 1
        log_eval(f"Preparing: {node.to_str()}", _eval_depth)
        left = evaluate_ast(node.left, base, cache)
        right = evaluate_ast(node.right, base, cache)
        _eval_depth -= 1

        op = node.op.value
        log_eval(f"Evaluating: {Colors.BLUE}{left!r}{Colors.ENDC} {Colors.WHITE}{op}{Colors.ENDC} {Colors.BLUE}{right!r}{Colors.ENDC}", _eval_depth)

        if op == '+': result = left + right
        elif op == '-': result = left - right
        elif op == '*': result = left * right
        elif op == '/':
            result = AoPValue.from_number(left.to_numerical() // right.to_numerical(), base=base)
        elif op in ('^', '**'):
            if isinstance(node.left, IdentifierNode) and node.left.name == 'j' and isinstance(node.right, IdentifierNode):
                 right_exp = LETTER_TO_EXPONENT_MAP.get(node.right.name[0], 0)
                 new_exponent = 10**right_exp
                 result = AoPValue({new_exponent: 1}, base=base)
            else:
                 result = left ** right

    if result is not None:
        log_eval(f"Result of {Colors.WHITE}'{node_str}'{Colors.ENDC} is {Colors.BLUE}{result!r}{Colors.ENDC}", _eval_depth)
        # --- NEW: Update sub-expression cache before returning ---
        if cache is not None: # Avoid duplicating top-level cache entry if needed
            if base_str not in cache: cache[base_str] = {}
            # Only store the pickle for sub-expressions, as formatting is not needed here.
            pickled_obj = pickle.dumps(result)
            b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
            cache[base_str][node_str] = {"raw_pickle": b64_pickle}
            # Note: We don't set cache_dirty here; the top-level calculator manages that flag.
        return result

    raise TypeError(f"Unknown AST node type: {type(node)}")
