# aopl_python_impl/aop_parser.py
import re, logging
from typing import List, Dict
from .definitions import OPERATORS, Token, AoPError
from .aop_value import AoPValue
from .interfaces import TermGetter
# FIX: Do not import aop_operations at the top level to avoid circular import issues.
# from . import aop_operations as ops

def _handle_op(stack: list[AoPValue], base: int, token: Token, op_func):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for {token.value}", token)
    op2, op1 = stack.pop(), stack.pop()
    stack.append(op_func(op1, op2, base))

# FIX: Import ops inside each handler function
def _handle_add(stack: list[AoPValue], base: int, token: Token):
    from . import aop_operations as ops
    _handle_op(stack, base, token, ops.add_values)
def _handle_subtract(stack: list[AoPValue], base: int, token: Token):
    from . import aop_operations as ops
    _handle_op(stack, base, token, ops.subtract_values)
def _handle_multiply(stack: list[AoPValue], base: int, token: Token):
    from . import aop_operations as ops
    _handle_op(stack, base, token, ops.multiply_values)
def _handle_divide(stack: list[AoPValue], base: int, token: Token):
    from . import aop_operations as ops
    _handle_op(stack, base, token, ops.divide_values)
def _handle_power(stack: list[AoPValue], base: int, token: Token):
    from . import aop_operations as ops
    _handle_op(stack, base, token, ops.power_value)

def _handle_unary_minus_op(stack: list[AoPValue], base: int, token: Token): # New handler
    from . import aop_operations as ops # Import ops locally
    if not stack: raise AoPError("Insufficient operand for unary minus", token)
    # For AoP, unary minus is multiplying by -1.
    stack.append(ops.scalar_multiply(complex(-1.0), stack.pop(), base))

OPERATOR_HANDLERS = {'+': _handle_add, '-': _handle_subtract, '*': _handle_multiply, '/': _handle_divide, '^': _handle_power, '**': _handle_power}

# ... (rest of the file is unchanged)

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

        if current_token_kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL'):
            output_queue.append(token_obj)
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
    stack: list[AoPValue] = []
    UMINUS_INTERNAL_OP_NAME = '_UMINUS_'
    current_op_handlers = OPERATOR_HANDLERS.copy()
    current_op_handlers[UMINUS_INTERNAL_OP_NAME] = _handle_unary_minus_op

    for token in rpn_tokens:
        if token.kind in ('NUMBER', 'IDENTIFIER', 'VARIABLE', 'COEFF_WORD', 'CONSTANT_LITERAL'):
            stack.append(get_term_value_func(token.value, variables, token.kind))
            logging.debug(f"Pushed to stack: {stack[-1]!r}")
        elif token.kind == 'OPERATOR' or token.kind == 'IMPLICIT_OPERATOR' or token.value == UMINUS_INTERNAL_OP_NAME:
            if token.value in current_op_handlers:
                current_op_handlers[token.value](stack, base, token)
            else:
                raise AoPError(f"Unsupported operator: {token.value}", token)
    if len(stack) != 1:
        raise AoPError("Invalid expression: check operators and operands.", rpn_tokens[-1] if rpn_tokens else None)
    logging.debug(f"Final RPN result: {stack[0]!r}")
    return stack[0]
