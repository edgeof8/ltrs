# aopl_python_impl/aop_parser.py
import re, logging
from typing import List, Dict, Union
from .definitions import OPERATORS, Token, AoPError, LETTER_TO_EXPONENT_MAP
from .aop_value import AoPValue
from .interfaces import TermGetter
# Do not import aop_operations at the top level to avoid circular import issues.

def _resolve_variable(operand: Union[AoPValue, Token], variables: Dict[str, AoPValue], get_term_value_func: TermGetter) -> AoPValue:
    """Helper to resolve a variable Token to its AoPValue."""
    if isinstance(operand, Token) and operand.kind == 'VARIABLE':
        # This is where we look up the variable's value
        return get_term_value_func(operand.value, variables, operand.kind)
    elif isinstance(operand, AoPValue):
        return operand
    # Should not happen if stack contains only AoPValues or VARIABLE Tokens
    raise AoPError(f"Unexpected item on stack for operation: {operand!r}")

def _handle_op(stack: list[Union[AoPValue, Token]], variables: Dict[str, AoPValue], get_term_value_func: TermGetter, base: int, token: Token, op_func):
    """Generalized handler for binary operators that resolves variables."""
    if len(stack) < 2: raise AoPError(f"Insufficient operands for {token.value}", token)
    op2_raw, op1_raw = stack.pop(), stack.pop()
    # Resolve operands to AoPValues before performing the operation
    op1 = _resolve_variable(op1_raw, variables, get_term_value_func)
    op2 = _resolve_variable(op2_raw, variables, get_term_value_func)
    stack.append(op_func(op1, op2, base))

def _handle_add(stack, variables, get_term_value_func, base, token):
    from . import aop_operations as ops
    _handle_op(stack, variables, get_term_value_func, base, token, ops.add_values)
def _handle_subtract(stack, variables, get_term_value_func, base, token):
    from . import aop_operations as ops
    _handle_op(stack, variables, get_term_value_func, base, token, ops.subtract_values)
def _handle_multiply(stack, variables, get_term_value_func, base, token):
    from . import aop_operations as ops
    _handle_op(stack, variables, get_term_value_func, base, token, ops.multiply_values)
def _handle_divide(stack, variables, get_term_value_func, base, token):
    from . import aop_operations as ops
    _handle_op(stack, variables, get_term_value_func, base, token, ops.divide_values)
def _handle_power(stack, variables, get_term_value_func, base, token):
    from . import aop_operations as ops
    _handle_op(stack, variables, get_term_value_func, base, token, ops.power_value)

def _handle_assignment(stack: list[Union[AoPValue, Token]], variables: Dict[str, AoPValue], get_term_value_func: TermGetter, token: Token):
    if len(stack) < 2: raise AoPError("Insufficient operands for assignment", token)
    value_to_assign_raw = stack.pop()
    var_token = stack.pop()
    if not isinstance(var_token, Token) or var_token.kind != 'VARIABLE':
        raise AoPError(f"Invalid L-value for assignment: {var_token!r}", token)
    # The RHS of an assignment can also be a variable, so it must be resolved
    value_to_assign = _resolve_variable(value_to_assign_raw, variables, get_term_value_func) if isinstance(value_to_assign_raw, Token) else value_to_assign_raw
    variables[var_token.value] = value_to_assign
    stack.append(value_to_assign)

def _handle_equals(stack, variables, get_term_value_func, base, token):
    from . import aop_operations as ops
    _handle_op(stack, variables, get_term_value_func, base, token, ops.equals_values)

def _handle_unary_minus_op(stack: list[Union[AoPValue, Token]], variables: Dict[str, AoPValue], get_term_value_func: TermGetter, base: int, token: Token):
    if not stack: raise AoPError("Insufficient operand for unary minus", token)
    operand_raw = stack.pop()
    resolved_operand = _resolve_variable(operand_raw, variables, get_term_value_func)
    from . import aop_operations as ops
    stack.append(ops.scalar_multiply(complex(-1.0), resolved_operand, base))

OPERATOR_HANDLERS = {
    '+': _handle_add, '-': _handle_subtract, '*': _handle_multiply, '/': _handle_divide,
    '^': _handle_power, '**': _handle_power, '==': _handle_equals
}


def insert_implicit_multiplication(tokens: List[Token]) -> List[Token]:
    """
    This is the key to fixing expressions like '2a' and 'a(b+c)'.
    It inserts a multiplication token '*' where it's implied.
    """
    result = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        result.append(token)
        if i + 1 < len(tokens):
            next_token = tokens[i+1]
            # A value-like token is anything that's not an operator or right parenthesis.
            is_val_like = token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL', 'RPAREN')
            # The next token can be a value or the start of a parenthetical group.
            is_next_val_like = next_token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL', 'LPAREN')

            if is_val_like and is_next_val_like:
                result.append(Token('IMPLICIT_OPERATOR', '*', -1, -1))
        i += 1
    return result

def tokenize_expression(expression: str, token_regex: re.Pattern) -> List[Token]:
    from .definitions import TOKEN_SPECIFICATION # Import here to avoid circular dependency issues at module load time
    full_regex = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))
    raw_tokens = []
    for match in full_regex.finditer(expression):
        kind = match.lastgroup
        if kind and kind != 'WHITESPACE' and kind != 'MISMATCH':
            raw_tokens.append(Token(kind, match.group(), match.start(), match.end()))
        elif kind == 'MISMATCH':
            raise AoPError(f"Unexpected character: '{match.group()}'", Token(kind, match.group(), match.start(), match.end()))
    logging.debug(f"Raw tokens: {raw_tokens}")
    # Normalize lowercase 'z' to uppercase 'Z' if 'Z' is a defined AoP letter.
    # This effectively makes 'z' an input alias for 'Z'.
    normalized_tokens_for_z_alias = []
    for rt_token in raw_tokens:  # Renamed loop variable to avoid conflict
        if rt_token.kind == 'IDENTIFIER' and rt_token.value == 'z' and 'Z' in LETTER_TO_EXPONENT_MAP:
            normalized_tokens_for_z_alias.append(rt_token._replace(value='Z'))
        else:
            normalized_tokens_for_z_alias.append(rt_token)
    raw_tokens = normalized_tokens_for_z_alias  # Update raw_tokens
    tokens = insert_implicit_multiplication(raw_tokens)
    logging.debug(f"Tokens after implicit multiplication: {tokens}")
    return tokens

def infix_to_rpn(tokens: List[Token], operators_map: Dict[str, Dict]) -> List[Token]:
    output_queue: List[Token] = []
    operator_stack: List[Token] = []

    # Implicit multiplication (e.g., '2b' or 'ab') must have the highest precedence to group terms before exponentiation.
    implicit_op_props = {'precedence': 6, 'associativity': 'left'}

    # Define a constant for the internal name of the unary minus operator
    UMINUS_INTERNAL_OP_NAME = '_UMINUS_'

    _operators_map_extended = operators_map.copy()
    # Unary minus precedence: higher than mul/div (3), and higher than power (5) to ensure correct binding.
    # Power is R-assoc. Unary minus is R-assoc.
    # To ensure a^-b is a^(-b), UMINUS needs to bind to 'b' before '^' considers '-b' as its RHS.
    _operators_map_extended[UMINUS_INTERNAL_OP_NAME] = {'precedence': 5.5, 'associativity': 'right'} # Higher than ^ (5)

    for i, token_obj in enumerate(tokens):
        current_token_value = token_obj.value
        current_token_kind = token_obj.kind
        is_identified_unary_op = False

        if current_token_kind == 'OPERATOR' and current_token_value == '-':
            # Context check for unary minus
            if i == 0 or tokens[i-1].kind in ('OPERATOR', 'LPAREN', 'IMPLICIT_OPERATOR'):
                is_identified_unary_op = True
                current_token_value = UMINUS_INTERNAL_OP_NAME # Reassign value for logic

        if current_token_kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL', 'VARIABLE'): # Add VARIABLE
            output_queue.append(token_obj) # Push VARIABLE token itself to RPN queue
        elif current_token_kind == 'OPERATOR' or token_obj.kind == 'IMPLICIT_OPERATOR': # Use token_obj.kind for implicit

            op_to_process = current_token_value # This might be UMINUS_INTERNAL_OP_NAME or original like '+'
            op_props = implicit_op_props if token_obj.kind == 'IMPLICIT_OPERATOR' else _operators_map_extended[op_to_process]

            while (operator_stack and operator_stack[-1].value != '('):
                stack_op_token = operator_stack[-1]
                # Stack op value could also be UMINUS_INTERNAL_OP_NAME
                stack_op_value_for_lookup = stack_op_token.value
                stack_op_props = implicit_op_props if stack_op_token.kind == 'IMPLICIT_OPERATOR' else _operators_map_extended[stack_op_value_for_lookup]

                if (stack_op_props['precedence'] > op_props['precedence']) or \
                   (stack_op_props['precedence'] == op_props['precedence'] and op_props['associativity'] == 'left'):
                    output_queue.append(operator_stack.pop())
                else:
                    break
            # Push the original token_obj, but replace its .value if it was identified as unary
            operator_stack.append(token_obj._replace(value=op_to_process))
        elif current_token_kind == 'LPAREN':
            operator_stack.append(token_obj)
        elif current_token_kind == 'RPAREN':
            while operator_stack and operator_stack[-1].value != '(':
                output_queue.append(operator_stack.pop())
            if not operator_stack: raise AoPError("Mismatched parentheses", token_obj)
            operator_stack.pop()

    while operator_stack:
        stack_top_token = operator_stack.pop()
        if stack_top_token.value == '(':
            raise AoPError("Mismatched parentheses", stack_top_token)
        output_queue.append(stack_top_token)

    logging.debug(f"RPN queue: {output_queue}")
    return output_queue

def evaluate_rpn(rpn_tokens: List[Token], variables: Dict[str, AoPValue], get_term_value_func: TermGetter, base: int) -> AoPValue:
    stack: list[Union[AoPValue, Token]] = [] # Stack can hold values or variable tokens
    UMINUS_INTERNAL_OP_NAME = '_UMINUS_'

    for token in rpn_tokens:
        if token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL'):
            stack.append(get_term_value_func(token.value, variables, token.kind))
            logging.debug(f"Pushed to stack: {stack[-1]!r}")
        elif token.kind == 'VARIABLE':
            # For variables, push the token itself. It will be resolved by operators that use it.
            stack.append(token)
            logging.debug(f"Pushed to stack (as L-value): {stack[-1]!r}")
        elif token.value == '=':
            # Assignment is special: LHS is a token, RHS must be resolved.
            _handle_assignment(stack, variables, get_term_value_func, token)
        elif token.value == UMINUS_INTERNAL_OP_NAME:
            # Unary minus is special: operates on one operand which might be a token.
            _handle_unary_minus_op(stack, variables, get_term_value_func, base, token)
        elif token.value in OPERATOR_HANDLERS:
            # Other binary operators use the generalized handler.
            OPERATOR_HANDLERS[token.value](stack, variables, get_term_value_func, base, token)
        else:
            raise AoPError(f"Unsupported operator or logic error: {token.value}", token)

    # After the loop, the stack should have one final AoPValue
    if len(stack) != 1 or not isinstance(stack[0], AoPValue):
        # If final item is a token, it was likely an unresolved variable
        final_result = stack[0]
        if isinstance(final_result, Token) and final_result.kind == 'VARIABLE':
            final_result = _resolve_variable(final_result, variables, get_term_value_func)
            stack[0] = final_result
        else: # Some other invalid final stack state
            raise AoPError("Invalid expression: check operators and operands.", rpn_tokens[-1] if rpn_tokens else None)

    logging.debug(f"Final RPN result: {stack[0]!r}")
    return stack[0]
