# aopl_python_impl/aop_parser.py
import re
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
                result.append(Token('OPERATOR', '*', -1, -1))
        i += 1
    return result

def tokenize_expression(expression: str, token_regex: re.Pattern) -> List[Token]:
    from .definitions import TOKEN_SPECIFICATION # Import here to avoid circular dependency issues at module load time
    full_regex = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))
    tokens = []
    for match in full_regex.finditer(expression):
        kind = match.lastgroup
        if kind and kind != 'WHITESPACE' and kind != 'MISMATCH':
            tokens.append(Token(kind, match.group(), match.start(), match.end()))
        elif kind == 'MISMATCH':
            raise AoPError(f"Unexpected character: '{match.group()}'", Token(kind, match.group(), match.start(), match.end()))
    return insert_implicit_multiplication(tokens)

def infix_to_rpn(tokens: List[Token], operators_map: Dict[str, Dict]) -> List[Token]:
    output_queue: List[Token] = []
    operator_stack: List[Token] = []
    for token in tokens:
        if token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL'):
            output_queue.append(token)
        elif token.kind == 'OPERATOR':
            while (operator_stack and operator_stack[-1].value != '(' and
                   ( (operators_map[operator_stack[-1].value]['precedence'] > operators_map[token.value]['precedence']) or
                     (operators_map[operator_stack[-1].value]['precedence'] == operators_map[token.value]['precedence'] and
                      operators_map[token.value]['associativity'] == 'left') ) ):
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
        elif token.kind == 'LPAREN':
            operator_stack.append(token)
        elif token.kind == 'RPAREN':
            while operator_stack and operator_stack[-1].value != '(':
                output_queue.append(operator_stack.pop())
            if not operator_stack: raise AoPError("Mismatched parentheses", token)
            operator_stack.pop()
    while operator_stack:
        if operator_stack[-1].value == '(': raise AoPError("Mismatched parentheses", operator_stack[-1])
        output_queue.append(operator_stack.pop())
    return output_queue

def evaluate_rpn(rpn_tokens: List[Token], variables: Dict[str, AoPValue], get_term_value_func: TermGetter, base: int) -> AoPValue:
    stack: list[AoPValue] = []
    for token in rpn_tokens:
        if token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL'):
            stack.append(get_term_value_func(token.value, variables, token.kind))
        elif token.kind == 'OPERATOR':
            if token.value in OPERATOR_HANDLERS:
                OPERATOR_HANDLERS[token.value](stack, base, token)
            else:
                raise AoPError(f"Unsupported operator: {token.value}", token)
    if len(stack) != 1:
        raise AoPError("Invalid expression: check operators and operands.", rpn_tokens[-1] if rpn_tokens else None)
    return stack[0]
