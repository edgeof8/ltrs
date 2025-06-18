# aopl_python_impl/aop_parser.py
import re
from typing import List, Dict
from .definitions import OPERATORS, Token, AoPError
from .aop_value import AoPValue
from .interfaces import TermGetter
from .aop_operations import add_values, subtract_values, multiply_values, divide_values, power_value as engine

def _handle_op(stack: list[AoPValue], base: int, token: Token, op_func):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for {token.value}", token)
    op2, op1 = stack.pop(), stack.pop()
    stack.append(op_func(op1, op2, base))

def _handle_add(stack: list[AoPValue], base: int, token: Token): _handle_op(stack, base, token, add_values)
def _handle_subtract(stack: list[AoPValue], base: int, token: Token): _handle_op(stack, base, token, subtract_values)
def _handle_multiply(stack: list[AoPValue], base: int, token: Token): _handle_op(stack, base, token, multiply_values)
def _handle_divide(stack: list[AoPValue], base: int, token: Token): _handle_op(stack, base, token, divide_values)
def _handle_power(stack: list[AoPValue], base: int, token: Token): _handle_op(stack, base, token, engine)

OPERATOR_HANDLERS = {'+': _handle_add, '-': _handle_subtract, '*': _handle_multiply, '/': _handle_divide, '^': _handle_power, '**': _handle_power}
# (Rest of parser logic is stable and correct)
# ...

def insert_implicit_multiplication(tokens: List[Token]) -> List[Token]:
    result = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        result.append(token)
        if i + 1 < len(tokens):
            next_token = tokens[i+1]
            # Rule: Insert '*' between two terms if they are not separated by an operator.
            # A term can be a NUMBER, IDENTIFIER, COEFF_WORD, or a group in parentheses (ending in RPAREN).
            # The next term can be a NUMBER, IDENTIFIER, COEFF_WORD, or a group in parentheses (starting with LPAREN).
            if (token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'RPAREN') and
                next_token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'LPAREN')):
                # Exception: Do not insert if it's for a power's parenthesized exponent, like `a^(b*c)`
                if not (token.kind == 'IDENTIFIER' and next_token.kind == 'LPAREN' and i > 0 and tokens[i-1].value in ('^', '**')):
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
