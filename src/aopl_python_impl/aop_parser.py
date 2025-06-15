# aopl_python_impl/aop_parser.py

from typing import List, Tuple, Union, Optional
from .definitions import ValueTuple, Operator, PowerAssociativity
from .aop_operations import is_symbolic_exponent

class ParseError(Exception):
    pass

def tokenize(expression: str) -> List[str]:
    expression = expression.replace(' ', '')
    tokens = []
    i = 0
    while i < len(expression):
        char = expression[i]
        if char.isdigit() or (char == '-' and (i == 0 or expression[i-1] in '(,+*^/')):
            start = i
            i += 1
            while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
                i += 1
            tokens.append(expression[start:i])
            continue
        elif char.isalpha():
            tokens.append(char)
            i += 1
            continue
        elif char in '(,+*^/)':
            tokens.append(char)
            i += 1
            continue
        else:
            raise ParseError(f"Unexpected character '{char}' at position {i}")
    return tokens

def precedence(op: str, power_assoc_setting: PowerAssociativity) -> int:
    if op == '+' or op == ',':
        return 1
    elif op == '*':
        return 2
    elif op == '/':
        return 3
    elif op == '^':
        return 4 if power_assoc_setting == PowerAssociativity.RIGHT else 5
    return 0

def is_operator(token: str) -> bool:
    return token in ['+', ',', '*', '/', '^']

def to_rpn(tokens: List[str], power_assoc_setting: PowerAssociativity) -> List[str]:
    output = []
    operators = []
    for token in tokens:
        if token.isalpha() or token.replace('.', '').replace('-', '').isdigit():
            output.append(token)
        elif token == '(':
            operators.append(token)
        elif token == ')':
            while operators and operators[-1] != '(':
                output.append(operators.pop())
            if operators:
                operators.pop()  # Remove '('
            else:
                raise ParseError("Mismatched parentheses")
        elif is_operator(token):
            while (operators and operators[-1] != '(' and
                   precedence(operators[-1], power_assoc_setting) >= precedence(token, power_assoc_setting)):
                output.append(operators.pop())
            operators.append(token)
    while operators:
        op = operators.pop()
        if op in '()':
            raise ParseError("Mismatched parentheses")
        output.append(op)
    return output

def evaluate_rpn(rpn: List[str], base: int, letter_to_val_func) -> ValueTuple:
    stack = []
    for token in rpn:
        if token.isalpha():
            stack.append(letter_to_val_func(token, base))
        elif token.replace('.', '').replace('-', '').isdigit():
            stack.append((float(token), 0))
        elif is_operator(token):
            if len(stack) < 2:
                raise ParseError("Insufficient operands for operator")
            b = stack.pop()
            a = stack.pop()
            if token == '+':
                from .aop_operations import add_values
                stack.append(add_values(a, b, base))
            elif token == ',':
                from .aop_operations import subtract_values
                stack.append(subtract_values(a, b, base))
            elif token == '*':
                from .aop_operations import multiply_values
                stack.append(multiply_values(a, b))
            elif token == '/':
                from .aop_operations import divide_values
                stack.append(divide_values(a, b))
            elif token == '^':
                from .aop_operations import power_values
                stack.append(power_values(a, b, base))
    if len(stack) != 1:
        raise ParseError("Invalid expression: too many operands")
    return stack[0]

def letter_to_value(letter: str, base: int) -> ValueTuple:
    if not letter.isalpha() or len(letter) != 1:
        raise ValueError(f"Expected a single letter, got '{letter}'")
    val = ord(letter.lower()) - ord('a') + 1
    if val < 1 or val > 26:
        raise ValueError(f"Letter '{letter}' out of range a-z")
    if val == 1: # 'a' is base^1
        return (1.0, 1)
    elif val == 2: # 'b' is base^2
        return (1.0, 2)
    elif val == 3: # 'c' is base^3
        return (1.0, 3)
    else:
        # For higher letters, we use base^val directly
        return (1.0, val)

def parse_and_evaluate(expression: str, base: int, power_assoc_setting: PowerAssociativity = PowerAssociativity.RIGHT) -> ValueTuple:
    if not expression:
        raise ParseError("Empty expression")
    tokens = tokenize(expression)
    rpn = to_rpn(tokens, power_assoc_setting)
    result = evaluate_rpn(rpn, base, letter_to_value)
    from .aop_operations import simplify_value
    return simplify_value(result, base)
