# aopl_python_impl/aop_parser.py

import re
from typing import List, Dict

DEBUG_AOP_PARSER = True # Global debug flag for this module

from .definitions import OPERATORS, Token, AoPError
from .aop_value import AoPValue
from .interfaces import TermGetter
from . import aop_operations

# ... (handlers are the same) ...
def _handle_add(stack: list[AoPValue], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for operator '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_add] op1: {op1}, op2: {op2}")
    try:
        res = aop_operations.add_values(op1, op2, base)
        if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_add] result: {res}")
        stack.append(res)
    except OverflowError as oe:
        if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_add] OverflowError: {oe}")
        raise # Re-raise to be caught by AoP_Calculator

def _handle_subtract(stack: list[AoPValue], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for operator '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_subtract] op1: {op1}, op2: {op2}")
    try:
        res = aop_operations.subtract_values(op1, op2, base)
        if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_subtract] result: {res}")
        stack.append(res)
    except OverflowError as oe:
        if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_subtract] OverflowError: {oe}")
        raise # Re-raise to be caught by AoP_Calculator

def _handle_multiply(stack: list[AoPValue], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for operator '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_multiply] op1: {op1}, op2: {op2}")
    res_mult = aop_operations.multiply_values(op1, op2)
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_multiply] mult_res: {res_mult}")
    res_simple = aop_operations.simplify_value(res_mult, base)
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_multiply] simplified_res: {res_simple}")
    stack.append(res_simple)

def _handle_divide(stack: list[AoPValue], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for operator '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_divide] op1: {op1}, op2: {op2}")
    res_div = aop_operations.divide_values(op1, op2)
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_divide] div_res: {res_div}")
    res_simple = aop_operations.simplify_value(res_div, base)
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_divide] simplified_res: {res_simple}")
    stack.append(res_simple)

def _handle_power(stack: list[AoPValue], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for '{token.value}'", token)
    power_val = stack.pop()
    base_val = stack.pop()
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_power] base_val: {base_val}, power_val: {power_val}")
    res = aop_operations.power_value(base_val, power_val, base)
    if DEBUG_AOP_PARSER: print(f"[DEBUG _handle_power] result: {res}")
    # Power results are often simplified within power_value or by subsequent operations.
    # For now, not simplifying again here unless specific issues arise.
    stack.append(res)

OPERATOR_HANDLERS = {
    '+': _handle_add,
    '-': _handle_subtract,
    '*': _handle_multiply,
    '/': _handle_divide,
    '^': _handle_power,
    '**': _handle_power,
}

# ... (tokenize is the same) ...
def insert_implicit_multiplication(tokens: List[Token]) -> List[Token]:
    result_tokens: List[Token] = []
    for i, token in enumerate(tokens):
        result_tokens.append(token)
        if i + 1 < len(tokens):
            next_token = tokens[i+1]
            if (token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'RPAREN') and
                next_token.kind in ('IDENTIFIER', 'COEFF_WORD', 'LPAREN', 'NUMBER')):
                 result_tokens.append(Token('OPERATOR', '*', -1, -1))
    return result_tokens

def tokenize_expression(expression: str, token_regex: re.Pattern) -> List[Token]:
    tokens: List[Token] = []
    for match in token_regex.finditer(expression):
        kind = match.lastgroup
        assert kind is not None, "Internal tokenizer error"
        if kind == 'WHITESPACE': continue
        if kind == 'MISMATCH':
            raise AoPError(f"Unexpected character: '{match.group()}'", Token(kind, match.group(), match.start(), match.end()))
        tokens.append(Token(kind, match.group(), match.start(), match.end()))
    return insert_implicit_multiplication(tokens)


def infix_to_rpn(tokens: List[Token], operators_map: Dict[str, Dict]) -> List[Token]:
    # This function is now the key. We force right-associativity for '^'.
    output_queue: List[Token] = []
    operator_stack: List[Token] = []
    for token in tokens:
        if token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL'):
            output_queue.append(token)
        elif token.kind == 'OPERATOR':
            # THIS IS THE CHANGE
            # For right-associative operators like '^', the condition is different.
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
            if operator_stack: operator_stack.pop()
            else: raise AoPError("Mismatched parentheses", token)
    while operator_stack:
        if operator_stack[-1].value == '(': raise AoPError("Mismatched parentheses", operator_stack[-1])
        output_queue.append(operator_stack.pop())
    return output_queue

# ... (evaluate_rpn is the same) ...
def evaluate_rpn(rpn_tokens: List[Token], variables: Dict[str, AoPValue], get_term_value_func: TermGetter, base: int) -> AoPValue:
    operand_stack: list[AoPValue] = []
    if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] RPN Tokens: {[t.value for t in rpn_tokens]}")
    for token_idx, token in enumerate(rpn_tokens):
        if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] Processing token {token_idx}: {token.kind} '{token.value}'")
        if token.kind in ('NUMBER', 'IDENTIFIER', 'COEFF_WORD', 'CONSTANT_LITERAL'):
            term_val = get_term_value_func(token.value, variables, token.kind)
            if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] Pushing operand: {term_val} for token '{token.value}'")
            operand_stack.append(term_val)
        elif token.kind == 'OPERATOR':
            if token.value in OPERATOR_HANDLERS:
                if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] Applying operator: {token.value}. Stack before: {operand_stack}")
                OPERATOR_HANDLERS[token.value](operand_stack, base, token)
                if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] Stack after operator {token.value}: {operand_stack}")
            else: raise AoPError(f"Unknown operator: {token.value}", token)
        if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] Current operand_stack: {operand_stack}")

    if len(operand_stack) != 1:
        if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] ERROR: Invalid final stack: {operand_stack}")
        raise AoPError(f"Invalid expression: stack has {len(operand_stack)} items after evaluation")

    final_result = operand_stack[0]
    if DEBUG_AOP_PARSER: print(f"[DEBUG evaluate_rpn] Final result: {final_result}")
    return final_result
