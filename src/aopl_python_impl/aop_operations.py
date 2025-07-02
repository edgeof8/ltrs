# aopl_python_impl/aop_operations.py
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode, SymbolicPowerNode, AopLiteralNode
from .definitions import LETTER_TO_EXPONENT_MAP, AoPError, EXPONENT_TO_LETTER_MAP, int_to_key, SymbolicPowerResult, Token
from .aop_value import AoPValue
import logging
import pickle
import base64
from .aop_logger import log_eval, Colors, log_pow
from .aop_parser import Parser

_eval_depth = 0

def evaluate_ast(node: ASTNode, base: int, cache: dict | None = None) -> 'AoPValue | SymbolicPowerResult':
    global _eval_depth
    node_str = node.to_str()
    base_str = str(base)
    if cache and base_str in cache and node_str in cache[base_str]:
        cached_data = cache[base_str][node_str]
        if "raw_pickle" in cached_data:
            logging.debug(f"Sub-expression cache hit for '{node_str}'. Unpickling.")
            pickle_data = base64.b64decode(cached_data["raw_pickle"])
            return pickle.loads(pickle_data)

    result: 'AoPValue | SymbolicPowerResult'
    if isinstance(node, NumberNode):
        val = AoPValue.from_number(int(node.token.value), base=base)
        log_eval(f"Interpreted number {Colors.WHITE}'{node.token.value}'{Colors.ENDC} -> {Colors.BLUE}{val!r}{Colors.ENDC}", _eval_depth)
        result = val
    elif isinstance(node, AopLiteralNode):
        log_eval(f"Evaluating AOP_LITERAL: {Colors.WHITE}'{node.value}'{Colors.ENDC}", _eval_depth)
        total_val = AoPValue(poly=None, base=base) # Use the public constructor
        import re
        term_pattern = re.compile(r'(\d*\.?\d*[a-zA-Z]|\d+\.?\d*)')
        terms = term_pattern.findall(node.value)
        for term_str in terms:
            dummy_token = Token('TERM', term_str, 0, 0)
            if term_str.replace('.', '').isnumeric():
                term_node = NumberNode(dummy_token)
            else:
                term_node = IdentifierNode(dummy_token)
            term_value = evaluate_ast(term_node, base, cache)
            if isinstance(term_value, AoPValue):
                total_val += term_value
        log_eval(f"Result of AOP_LITERAL {Colors.WHITE}'{node.value}'{Colors.ENDC} -> {Colors.BLUE}{total_val!r}{Colors.ENDC}", _eval_depth)
        result = total_val
    elif isinstance(node, IdentifierNode):
        # --- THIS BLOCK IS THE CRITICAL FIX ---
        import re
        # This regex handles a single term like '2b' or 'c'.
        # It correctly separates the optional coefficient from the single letter.
        match = re.match(r'^(\d*\.?\d*)?([a-zA-Z])$', node.token.value)

        if not match:
            raise ValueError(f"Invalid identifier format received by evaluator: '{node.token.value}'")

        coeff_str, letter = match.groups()

        # Determine the coefficient (defaults to 1)
        coeff = int(float(coeff_str)) if coeff_str else 1

        # Get the exponent value for the letter
        exponent_val = LETTER_TO_EXPONENT_MAP.get(letter, 0)

        # The key for the poly dictionary MUST be the numerical exponent as a string.
        poly_key_str = str(exponent_val)

        # Create the dictionary in the format Rust's constructor expects.
        poly_for_rust = {poly_key_str: coeff}

        val = AoPValue(poly=poly_for_rust, base=base)

        log_eval(f"Interpreted term {Colors.WHITE}'{node.name}'{Colors.ENDC} -> {Colors.BLUE}{val!r}{Colors.ENDC}", _eval_depth)
        result = val
    elif isinstance(node, UnaryOpNode):
        _eval_depth += 1
        right = evaluate_ast(node.right, base, cache)
        _eval_depth -= 1
        if node.op.value == '-':
            if isinstance(right, AoPValue):
                result = right * AoPValue.from_number(-1, base=base)
            else:
                raise ValueError("Cannot apply unary minus to non-AoPValue")
        else:
            result = right
    elif isinstance(node, BinaryOpNode):
        _eval_depth += 1
        log_eval(f"Preparing: {node.to_str()}", _eval_depth)
        left = evaluate_ast(node.left, base, cache)
        right = evaluate_ast(node.right, base, cache)
        _eval_depth -= 1
        op = node.op.value
        log_eval(f"Evaluating: {Colors.BLUE}{left!r}{Colors.WHITE}{op}{Colors.BLUE}{right!r}{Colors.ENDC}", _eval_depth)
        if op in ('^', '**'):
            if isinstance(left, AoPValue) and isinstance(right, AoPValue):
                result = SymbolicPowerResult(left, right)
            else:
                raise ValueError("Cannot create power operation with non-AoPValue types")
        else:
            left_val = left.resolve() if isinstance(left, SymbolicPowerResult) else left
            right_val = right.resolve() if isinstance(right, SymbolicPowerResult) else right
            if isinstance(left_val, AoPValue) and isinstance(right_val, AoPValue):
                if op == '+': result = left_val + right_val
                elif op == '-': result = left_val - right_val
                elif op == '*': result = left_val * right_val
                elif op == '/': result = AoPValue.from_number(left_val.to_numerical() // right_val.to_numerical(), base=base)
            else:
                raise ValueError(f"Cannot perform operation '{op}' on non-AoPValue types")

    log_eval(f"Result of {Colors.WHITE}'{node_str}'{Colors.ENDC} is {Colors.BLUE}{result!r}{Colors.ENDC}", _eval_depth)
    if cache is not None:
        if base_str not in cache: cache[base_str] = {}
        if isinstance(result, AoPValue):
            pickled_obj = pickle.dumps(result)
            b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
            cache[base_str][node_str] = {"raw_pickle": b64_pickle}
    return result

    raise TypeError(f"Unknown AST node type: {type(node)}")
