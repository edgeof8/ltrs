# aopl_python_impl/aop_parser.py

import re
import math
import cmath
from typing import Callable
from .definitions import ValueTuple, OPERATORS, Token, AoPError, TOKEN_SPECIFICATION
from .interfaces import TermGetter
from . import aop_operations

# --- Operator Handlers ---
def _handle_add(stack: list[ValueTuple], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    stack.append(aop_operations.add_values(op1, op2, base))

def _handle_subtract(stack: list[ValueTuple], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    stack.append(aop_operations.subtract_values(op1, op2, base))

def _handle_multiply(stack: list[ValueTuple], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    res = aop_operations.multiply_values(op1, op2)
    stack.append(aop_operations.simplify_value(res, base))

def _handle_divide(stack: list[ValueTuple], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for '{token.value}'", token)
    op2, op1 = stack.pop(), stack.pop()
    res = aop_operations.divide_values(op1, op2)
    stack.append(aop_operations.simplify_value(res, base))

# --- FINAL, FULLY SYMBOLIC POWER HANDLER ---
def _handle_power(stack: list[ValueTuple], base: int, token: Token):
    if len(stack) < 2: raise AoPError(f"Insufficient operands for operator '{token.value}'", token)
    power_vt = stack.pop()
    base_vt = stack.pop()

    # If the power is itself a pure symbolic term, we do symbolic math.
    if cmath.isclose(power_vt[0], 1.0) and base_vt[1] > 0:
        # This handles a^b, y^y, etc.
        # The new exponent is E_base * (B^E_power)
        try:
            power_numerical_exponent = base ** power_vt[1]
            new_exponent = base_vt[1] * power_numerical_exponent
            res = (base_vt[0], new_exponent)
        except OverflowError:
            raise OverflowError("Resulting exponent is too large.")
    else:
        # Otherwise, calculate the numerical value of the power.
        try:
            power_numerical = power_vt[0] * (base ** power_vt[1])
            if not math.isclose(power_numerical.imag, 0):
                raise AoPError(f"Power exponent must be real, got {power_numerical}", token)
            res = aop_operations.power_value(base_vt, power_numerical.real, base)
        except OverflowError:
            raise OverflowError(f"Power term '{power_vt}' is too large to evaluate numerically.")

    stack.append(aop_operations.simplify_value(res, base))
# --- END FINAL POWER HANDLER ---

def _handle_unary_minus(stack: list[ValueTuple], base: int, token: Token):
    if not stack: raise AoPError("Insufficient operands for unary minus", token)
    op_c, op_e = stack.pop()
    stack.append((-op_c, op_e))

def _handle_unary_plus(stack: list[ValueTuple], base: int, token: Token):
    if not stack: raise AoPError("Insufficient operands for unary plus", token)

OPERATOR_HANDLERS = {
    '+': _handle_add, '-': _handle_subtract, '*': _handle_multiply, '/': _handle_divide,
    '^': _handle_power, '_UMINUS': _handle_unary_minus, '_UPLUS': _handle_unary_plus
}

def _create_cmath_func_handler(func, domain_check=None, error_msg="Invalid input for function"):
    def handler(stack: list[ValueTuple], base: int, token: Token):
        if not stack: raise AoPError(f"Insufficient operands for function '{token.value}'", token)
        arg_vt = stack.pop()
        try:
            num_val = arg_vt[0] * (base ** arg_vt[1])
            if domain_check and not domain_check(num_val):
                raise AoPError(error_msg.format(val=num_val), token)
            result_complex = func(num_val)
            stack.append((result_complex, 0))
        except (ValueError, TypeError, OverflowError) as e:
            raise AoPError(str(e), token) from e
    return handler

def _handle_sqrt_complex(stack: list[ValueTuple], base: int, token: Token):
    if not stack: raise AoPError(f"Insufficient operands for function '{token.value}'", token)
    coeff, expon = stack.pop()
    if expon % 2 != 0:
        num_val = coeff * (base ** expon)
        sqrt_val = cmath.sqrt(num_val)
        final_coeff, final_expon = sqrt_val, 0
    else:
        sqrt_coeff = cmath.sqrt(coeff)
        final_coeff, final_expon = sqrt_coeff, expon // 2
    if math.isclose(final_coeff.real, 0.0) and final_coeff.imag < 0 and math.isclose(coeff.imag, 0.0) and coeff.real < 0.0:
        final_coeff = complex(0, -final_coeff.imag)
    stack.append((final_coeff, final_expon))

FUNCTION_HANDLERS = {
    'sqrt': _handle_sqrt_complex,
    'log': _create_cmath_func_handler(cmath.log10, domain_check=lambda z: z.real > 0 and math.isclose(z.imag, 0), error_msg="Log (base 10) error: input {val} must be a positive real number"),
    'ln': _create_cmath_func_handler(cmath.log, domain_check=lambda z: z.real > 0 and math.isclose(z.imag, 0), error_msg="Natural log error: input {val} must be a positive real number"),
    'log2': _create_cmath_func_handler(lambda z: cmath.log(z, 2), domain_check=lambda z: z.real > 0 and math.isclose(z.imag, 0), error_msg="Log (base 2) error: input {val} must be a positive real number"),
    'sin': _create_cmath_func_handler(cmath.sin), 'cos': _create_cmath_func_handler(cmath.cos), 'tan': _create_cmath_func_handler(cmath.tan),
    'asin': _create_cmath_func_handler(cmath.asin), 'acos': _create_cmath_func_handler(cmath.acos), 'atan': _create_cmath_func_handler(cmath.atan),
    'sinh': _create_cmath_func_handler(cmath.sinh), 'cosh': _create_cmath_func_handler(cmath.cosh), 'tanh': _create_cmath_func_handler(cmath.tanh),
}

def tokenize_expression(expression_str: str, token_regex: re.Pattern) -> list[Token]:
    tokens = []
    for mo in token_regex.finditer(expression_str):
        kind = mo.lastgroup
        if kind is None:
            raise ValueError("Token regex did not match a group, which should not happen")
        value, start, end = mo.group(), *mo.span()
        if kind == 'MISMATCH':
            if not value.isspace(): raise AoPError(f"Unexpected character '{value}'", Token(kind, value, start, end))
            continue
        tokens.append(Token(kind, value, start, end))
    return tokens

def infix_to_rpn(tokens: list[Token], operators_map: dict) -> list[Token]:
    output_queue, operator_stack = [], []
    term_end_kinds = ['UNITY', 'COEFF_WORD', 'IDENTIFIER', 'NUMBER', 'CONSTANT_LITERAL', 'RPAREN']
    last_token_kind: str | None = None
    def insert_implicit_multiplication(current_token):
        mult_token = Token('OPERATOR', '*', current_token.start, current_token.start)
        op_details = operators_map[mult_token.value]
        while (operator_stack and operator_stack[-1].kind != 'LPAREN' and
               (operators_map.get(operator_stack[-1].value, {}).get('precedence', -1) >= op_details['precedence'])):
            output_queue.append(operator_stack.pop())
        operator_stack.append(mult_token)
    for token in tokens:
        if token.kind in ['UNITY', 'COEFF_WORD', 'IDENTIFIER', 'NUMBER', 'CONSTANT_LITERAL']:
            if last_token_kind in term_end_kinds: insert_implicit_multiplication(token)
            output_queue.append(token)
        elif token.kind == 'FUNCTION':
            if last_token_kind in term_end_kinds: insert_implicit_multiplication(token)
            operator_stack.append(token)
        elif token.kind == 'LPAREN':
            if last_token_kind in term_end_kinds: insert_implicit_multiplication(token)
            operator_stack.append(token)
        elif token.kind == 'OPERATOR':
            is_unary = token.value in ['+', '-'] and (last_token_kind is None or last_token_kind in ['OPERATOR', 'LPAREN', 'FUNCTION', 'COMMA'])
            op_name = ('_UPLUS' if token.value == '+' else '_UMINUS') if is_unary else token.value
            if not is_unary and last_token_kind not in term_end_kinds:
                raise AoPError(f"Missing value before binary operator '{token.value}'", token)
            op_details = operators_map[op_name]
            while (operator_stack and operator_stack[-1].kind != 'LPAREN' and
                   ((operator_stack[-1].kind == 'FUNCTION') or
                    (operators_map.get(operator_stack[-1].value, {}).get('precedence', -1) > op_details['precedence']) or
                    (operators_map.get(operator_stack[-1].value, {}).get('precedence', -1) == op_details['precedence'] and op_details['associativity'] == 'left'))):
                output_queue.append(operator_stack.pop())
            operator_stack.append(Token('OPERATOR', op_name, token.start, token.end))
        elif token.kind == 'RPAREN':
            if last_token_kind == 'LPAREN': raise AoPError("Empty parentheses '()' are not allowed", token)
            while operator_stack and operator_stack[-1].kind != 'LPAREN':
                output_queue.append(operator_stack.pop())
            if not operator_stack or operator_stack[-1].kind != 'LPAREN': raise AoPError("Mismatched parentheses", token)
            operator_stack.pop()
            if operator_stack and operator_stack[-1].kind == 'FUNCTION':
                output_queue.append(operator_stack.pop())
        elif token.kind == 'COMMA':
            while operator_stack and operator_stack[-1].kind != 'LPAREN':
                output_queue.append(operator_stack.pop())
            if not operator_stack: raise AoPError("Comma outside function arguments", token)
        last_token_kind = token.kind
    while operator_stack:
        op = operator_stack.pop()
        if op.kind == 'LPAREN': raise AoPError("Mismatched parentheses", op)
        output_queue.append(op)
    return output_queue

def evaluate_rpn(rpn_tokens: list[Token], variables: dict[str, ValueTuple], get_term_value_func: TermGetter, base: int) -> ValueTuple:
    operand_stack: list[ValueTuple] = []
    term_kinds_for_eval = ['UNITY', 'COEFF_WORD', 'IDENTIFIER', 'NUMBER', 'CONSTANT_LITERAL']
    for token in rpn_tokens:
        try:
            if token.kind in term_kinds_for_eval:
                operand_stack.append(get_term_value_func(token.value, variables, token.kind))
            elif token.kind == 'OPERATOR':
                OPERATOR_HANDLERS[token.value](operand_stack, base, token)
            elif token.kind == 'FUNCTION':
                FUNCTION_HANDLERS[token.value](operand_stack, base, token)
            else:
                raise AoPError(f"Unknown token kind in RPN evaluation: {token.kind}", token)
        except (ValueError, ZeroDivisionError, TypeError, KeyError) as e:
            raise AoPError(str(e), token) from e
    if len(operand_stack) != 1:
        raise AoPError(f"Invalid RPN evaluation: stack has {len(operand_stack)} items at the end.")
    return operand_stack[0]
