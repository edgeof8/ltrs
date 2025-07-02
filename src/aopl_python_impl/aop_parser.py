# aopl_python_impl/aop_parser.py
import logging, re
from typing import List
from .definitions import Token, AoPError
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode, AopLiteralNode

OPERATORS: dict = {
    '=': {'precedence': 1, 'associativity': 'right'},
    '==': {'precedence': 1.5, 'associativity': 'left'},
    '+': {'precedence': 2, 'associativity': 'left'},
    '-': {'precedence': 2, 'associativity': 'left'},
    '*': {'precedence': 3, 'associativity': 'left'},
    '/': {'precedence': 3, 'associativity': 'left'},
    '^': {'precedence': 5, 'associativity': 'right'}, # Correctly defined as right-associative
    '**': {'precedence': 5, 'associativity': 'right'}
}

def tokenize_expression(expression: str) -> List[Token]:
    TOKEN_REGEX = re.compile(r"(\*\*|==|[+\-*/^()])")
    raw_parts = [p for p in TOKEN_REGEX.split(expression) if p]
    tokens = []
    pos = 0

    for part in raw_parts:
        part = part.strip()
        if not part: continue
        start_pos = expression.find(part, pos)
        end_pos = start_pos + len(part)
        pos = end_pos

        if part in "()":
            tokens.append(Token('LPAREN' if part == '(' else 'RPAREN', part, start_pos, end_pos))
        elif part in OPERATORS:
            tokens.append(Token('OPERATOR', part, start_pos, end_pos))
        else:
            # This is a sequence of numbers and letters, e.g., "2b5c" or "abc" or "5"
            # We treat the entire contiguous block as one literal.
            tokens.append(Token('AOP_LITERAL', part, start_pos, end_pos))

    logging.debug(f"Tokens: {tokens}")
    return tokens

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens; self.pos = -1; self.current_token = None
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self):
        return self.parse_expression()

    # --- NEW SHUNTING-YARD-LIKE PARSER ---
    def parse_expression(self, precedence=0):
        left = self.atom()

        while self.current_token and self.current_token.kind == 'OPERATOR' and OPERATORS.get(self.current_token.value, {}).get('precedence', -1) >= precedence:
            op = self.current_token
            op_info = OPERATORS[op.value]
            next_precedence = op_info['precedence']
            # For right-associative operators, we use a slightly lower precedence for the recursive call
            if op_info['associativity'] == 'left':
                next_precedence += 1

            self.advance()
            right = self.parse_expression(next_precedence)
            left = BinaryOpNode(left, op, right)

        return left

    def atom(self):
        token = self.current_token
        if not token:
            raise SyntaxError("Unexpected end of expression")

        if token.kind == 'AOP_LITERAL':
            self.advance()
            return AopLiteralNode(token)
        elif token.value == '(':
            self.advance()
            node = self.parse_expression(0) # Reset precedence inside parentheses
            if not self.current_token or self.current_token.value != ')':
                raise SyntaxError("Mismatched parentheses")
            self.advance()
            return node

        raise SyntaxError(f"Unexpected token: {token}")
