# aopl_python_impl/aop_parser.py
import logging, re
from typing import List
from .definitions import Token, AoPError, OPERATORS
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode

def tokenize_expression(expression: str) -> List[Token]:
    from .definitions import TOKEN_SPECIFICATION
    full_regex = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))
    tokens = []
    for match in full_regex.finditer(expression):
        kind = match.lastgroup
        if kind and kind not in ('WHITESPACE', 'MISMATCH'):
            tokens.append(Token(kind, match.group(), match.start(), match.end()))

    result, i = [], 0
    while i < len(tokens):
        result.append(tokens[i])
        if i + 1 < len(tokens):
            if tokens[i].kind in ('NUMBER', 'IDENTIFIER', 'RPAREN') and tokens[i+1].kind in ('NUMBER', 'IDENTIFIER', 'LPAREN'):
                result.append(Token('IMPLICIT_OPERATOR', '*', -1, -1))
        i += 1
    logging.debug(f"Tokens: {result}")
    return result

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens; self.pos = -1; self.current_token = None
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def get_precedence(self, token: Token | None) -> int:
        if token is None: return -1
        # Implicit multiplication has higher precedence than power
        if token.kind == 'IMPLICIT_OPERATOR': return 6
        if token.value in OPERATORS: return OPERATORS[token.value]['precedence']
        return -1

    def parse(self, precedence=0):
        if not self.current_token:
            raise AoPError("Unexpected end of expression.")

        token = self.current_token
        if token.value in ('+', '-'):
            self.advance()
            left = UnaryOpNode(token, self.parse(4)) # Unary precedence
        else:
            left = self.atom()

        while self.current_token and precedence < self.get_precedence(self.current_token):
            op_token = self.current_token
            self.advance()

            if op_token.value in ('^', '**'): # Right-associative
                right = self.parse(self.get_precedence(op_token) - 1)
            else: # Left-associative
                right = self.parse(self.get_precedence(op_token))

            left = BinaryOpNode(left, op_token, right)

        return left

    def atom(self):
        token = self.current_token
        if not token: raise AoPError("Unexpected end of expression")
        if token.kind == 'NUMBER': self.advance(); return NumberNode(token)
        if token.kind == 'IDENTIFIER': self.advance(); return IdentifierNode(token)
        if token.value == '(':
            self.advance(); node = self.parse()
            if not self.current_token or self.current_token.value != ')':
                raise AoPError("Mismatched parentheses")
            self.advance()
            return node
        raise AoPError(f"Unexpected token: {token}")
