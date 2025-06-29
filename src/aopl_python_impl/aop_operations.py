# aopl_python_impl/aop_operations.py
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode, SymbolicPowerNode
from .aop_symbolic_power import SymbolicPower
from .definitions import LETTER_TO_EXPONENT_MAP, AoPError, EXPONENT_TO_LETTER_MAP
from .aop_value import AoPValue, int_to_key
from .aop_types import SymbolicPowerResult
import logging
# --- NEW: Imports for pickling and encoding ---
import pickle
import base64
from .aop_logger import log_eval, Colors

# --- MODIFIED: _power_operation now contains the full dispatch for powers ---
# It's called by evaluate_ast
def _power_operation(base: AoPValue, exponent: AoPValue) -> 'AoPValue | SymbolicPowerResult':
    """
    The intelligent dispatcher for the power operation.
    Decides whether to compute immediately (eager) or return a symbolic representation (lazy).
    """
    # 1. Hyper-Fast Path (e.g., Z^e, (aZ)^b) - Base is a pure power
    if base.is_pure_power():
        base_exponent_val = base.get_single_exponent_value()
        k_val_as_aop = AoPValue.from_number(base_exponent_val, base.base)
        new_exponent_aop = k_val_as_aop * exponent # Perform multiplication symbolically
        final_exponent_num = new_exponent_aop.to_numerical() # This is where it can get huge but stays int

        # Return as AoPValue (eager)
        return AoPValue({int_to_key(final_exponent_num, base.base): 1}, base=base.base)

    # 2. General Eager Path (e.g., (2a+y)^b, 9^b) - Base is complex, but exponent is small and numerical
    # We use a heuristic for "small and numerical" exponent.
    try:
        exp_num = exponent.to_numerical()
        if exp_num >= 0 and exp_num <= 1000000: # Arbitrary threshold for "small enough"
            log_eval(f"POWER DISPATCHER: General Eager Path for base {base!r} ^ {exponent!r}", _eval_depth)
            return _exponentiate_aop_value(base, exponent) # Calls the actual exponentiation function
    except (ValueError, OverflowError):
        pass

    # 3. Lazy Path (e.g., (2a+Z)^b where Z is huge) - Base is complex, and exponent is large/complex
    log_eval(f"POWER DISPATCHER: Lazy Path for base {base!r} ^ {exponent!r}", _eval_depth)
    return SymbolicPowerResult(base, exponent) # Returns a lazy object

# --- NEW HELPER FUNCTION: This is the core exponentiation algorithm ---
# It will be called from _power_operation (eager) or from aop_calculator (lazy resolve)
def _exponentiate_aop_value(base: AoPValue, exponent_aop_value: AoPValue) -> AoPValue:
    """
    Performs exponentiation (base ^ exponent_aop_value) using exponentiation by squaring.
    This function always returns an AoPValue.
    """
    n_int = exponent_aop_value.to_numerical() # Convert exponent to integer for the loop

    # Pragmatic check for truly huge exponents that would hang even this
    if n_int < 0: raise ValueError("Exponent must be a non-negative integer.")
    if n_int > 100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000:
        raise OverflowError(f"Exponent is too large to compute numerically: {exponent_aop_value!r}")

    log_eval(f"⚡︎ Evaluating power numerically: ({base!r}) ^ {n_int}", _eval_depth)
    if n_int == 0: return AoPValue({int_to_key(0, base.base): 1}, base.base)
    if n_int == 1: return base

    result = AoPValue({int_to_key(0, base.base): 1}, base.base)
    current_base = base
    while n_int > 0:
        if n_int % 2 == 1: result *= current_base
        current_base *= current_base
        n_int //= 2
    return result

_eval_depth = 0

def evaluate_ast(node: ASTNode, base: int, cache: dict | None = None) -> 'AoPValue | SymbolicPowerResult':
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
    result: AoPValue | SymbolicPowerResult | None = None

    if isinstance(node, NumberNode):
        val = AoPValue.from_number(int(node.value), base=base)
        log_eval(f"Interpreted number {Colors.WHITE}'{node.value}'{Colors.ENDC} -> {Colors.BLUE}{val!r}{Colors.ENDC}", _eval_depth)
        result = val
    elif isinstance(node, IdentifierNode):
        import re
        # Updated regex for identifier to handle multiple letters as one "logical" term
        # The previous version assumed single letters, which might be why a*s was 'a^2a^'
        # This needs to handle 'abc' -> AoP({c:1, b:1, a:1})

        # For now, sticking to the current single-letter rule based on aop_parser
        # The regex in aop_parser.py should ensure this correctly matches `a` not `abc`.
        match = re.match(r'^(\d*)?([a-zA-Z])$', node.name)
        if not match:
            raise ValueError(f"Invalid identifier/term format: {node.name}")

        coeff_str, letters_str = match.groups()
        coeff = int(coeff_str) if coeff_str else 1
        exp = LETTER_TO_EXPONENT_MAP.get(letters_str, 0) # This still expects a single letter
        exp_key = int_to_key(exp, base) # This turns 1 to 'a', 2 to 'b', etc.

        val = AoPValue({exp_key: coeff}, base=base)
        log_eval(f"Interpreted term {Colors.WHITE}'{node.name}'{Colors.ENDC} -> {Colors.BLUE}{val!r}{Colors.ENDC}", _eval_depth)
        result = val
    elif isinstance(node, UnaryOpNode):
        _eval_depth += 1
        evaluated_right = evaluate_ast(node.right, base, cache)
        _eval_depth -= 1
        # Ensure resolved to AoPValue before operation
        if isinstance(evaluated_right, SymbolicPowerResult):
            resolved_right = _exponentiate_aop_value(evaluated_right.base, evaluated_right.exponent)
        else:
            resolved_right = evaluated_right

        if not isinstance(resolved_right, AoPValue): raise TypeError(f"Cannot apply unary operation to non-AoPValue: {resolved_right!r}")

        if node.op.value == '-':
            result = resolved_right * AoPValue({int_to_key(0, base): -1}, base=base)
        else: # Unary '+'
            result = resolved_right
    elif isinstance(node, BinaryOpNode):
        _eval_depth += 1
        log_eval(f"Preparing: {node.to_str()}", _eval_depth)
        evaluated_left = evaluate_ast(node.left, base, cache)
        evaluated_right = evaluate_ast(node.right, base, cache)
        _eval_depth -= 1

        op = node.op.value # Get the operator
        log_eval(f"Evaluating: {Colors.BLUE}{evaluated_left!r}{Colors.ENDC} {Colors.WHITE}{op}{Colors.ENDC} {Colors.BLUE}{evaluated_right!r}{Colors.ENDC}", _eval_depth)

        # Helper to resolve an object to an AoPValue if it's a SymbolicPowerResult
        def _resolve_operand(obj):
            if isinstance(obj, SymbolicPowerResult):
                return _exponentiate_aop_value(obj.base, obj.exponent)
            return obj

        # Resolve both left and right operands to AoPValue objects if they are SymbolicPowerResult
        # For power operations, the base might be a SymbolicPowerResult, but the exponent
        # usually has to be a concrete AoPValue or number for common algorithms.
        # The resolution here is for ALL binary operations.
        resolved_left = _resolve_operand(evaluated_left)
        resolved_right = _resolve_operand(evaluated_right) # Exponent will be resolved if it's a SymbolicPowerResult

        # Ensure both are AoPValue objects for standard arithmetic operations
        if not isinstance(resolved_left, AoPValue) or not isinstance(resolved_right, AoPValue):
            # This should ideally not happen if operands are parsed and evaluated correctly
            raise TypeError(f"Operands must be AoPValue after resolution for '{op}': {resolved_left!r} {op} {resolved_right!r}")

        else: # Both operands are now guaranteed to be AoPValue objects
            if op == '+': result = resolved_left + resolved_right
            elif op == '-': result = resolved_left - resolved_right
            elif op == '*': result = resolved_left * resolved_right
            elif op == '/':
                result = AoPValue.from_number(resolved_left.to_numerical() // resolved_right.to_numerical(), base=base)
            elif op in ('^', '**'): # This is the main power operator logic
                result = _power_operation(resolved_left, resolved_right)

    if result is not None: # This if block was moved outside the else
        log_eval(f"Result of {Colors.WHITE}'{node_str}'{Colors.ENDC} is {Colors.BLUE}{result!r}{Colors.ENDC}", _eval_depth)
        # --- NEW: Update sub-expression cache before returning ---
        if cache is not None: # Avoid duplicating top-level cache entry if needed
            if base_str not in cache: cache[base_str] = {}
            # Only store the pickle for sub-expressions, as formatting is not needed here.
            if isinstance(result, AoPValue):  # Only pickle AoPValue for now
                pickled_obj = pickle.dumps(result)
                b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
                cache[base_str][node_str] = {"raw_pickle": b64_pickle}
            elif isinstance(result, SymbolicPowerResult):  # Also store SymbolicPowerResult
                pickled_obj = pickle.dumps(result)
                b64_pickle = base64.b64encode(pickled_obj).decode('utf-8')
                cache[base_str][node_str] = {"raw_pickle": b64_pickle}
            # Note: We don't set cache_dirty here; the top-level calculator manages that flag.
        return result

    raise TypeError(f"Unknown AST node type: {type(node)}")
