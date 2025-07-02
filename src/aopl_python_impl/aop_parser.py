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
    '^': {'precedence': 5, 'associativity': 'right'},
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
        if not self.tokens:
            return None
        return self.parse_expression(0)

    def parse_expression(self, precedence: int):
        left = self.parse_prefix()

        while self.current_token and self.current_token.kind == 'OPERATOR':
            op_info = OPERATORS.get(self.current_token.value)
            if not op_info or op_info['precedence'] < precedence:
                break

            op_token = self.current_token
            self.advance()

            if op_info['associativity'] == 'right':
                right = self.parse_expression(op_info['precedence'])
            else:
                right = self.parse_expression(op_info['precedence'] + 1)

            left = BinaryOpNode(left, op_token, right)

        return left

    def parse_prefix(self):
        token = self.current_token
        if not token:
            raise SyntaxError("Unexpected end of expression")

        if token.kind == 'AOP_LITERAL':
            self.advance()
            return AopLiteralNode(token)
        elif token.value == '(':
            self.advance()
            node = self.parse_expression(0)
            if not self.current_token or self.current_token.value != ')':
                raise SyntaxError("Mismatched parentheses")
            self.advance()
            return node
        elif token.value in ('-', '+'):
            self.advance()
            operand = self.parse_expression(10)
            return UnaryOpNode(token, operand)

        raise SyntaxError(f"Unexpected token: {token}")
