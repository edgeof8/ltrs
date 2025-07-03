# aopl_python_impl/aop_parser.py
import logging, re
from typing import List
from .definitions import Token, AoPError, OPERATORS
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode

def tokenize_expression(expression: str) -> List[Token]:
    """
    A stateful tokenizer that understands the 'additive by default' grammar.
    It correctly tokenizes sequences like '2b3c' into a single AopLiteralNode.
    """
    # This regex will now handle explicit operators and parentheses.
    # We will handle literals (numbers, words) manually.
    token_regex = re.compile(r"(\*\*|==|[+\-*/^()])")
    raw_parts = [p.strip() for p in token_regex.split(expression) if p.strip()]
    tokens = []
    pos = 0
    for part in raw_parts:
        start_pos = expression.find(part, pos)
        end_pos = start_pos + len(part)
        pos = end_pos
        if part in OPERATORS:
            tokens.append(Token('OPERATOR', part, start_pos, end_pos))
        elif part == '(':
            tokens.append(Token('LPAREN', part, start_pos, end_pos))
        elif part == ')':
            tokens.append(Token('RPAREN', part, start_pos, end_pos))
        else:
            # Anything else is treated as an "AOP literal" to be parsed later.
            # This correctly groups 'a2b' as a single literal.
            tokens.append(Token('AOP_LITERAL', part, start_pos, end_pos))

    logging.debug(f"Tokens: {tokens}")
    return tokens

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = -1
        self.current_token: Token | None = None
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self, precedence=0):
        if not self.tokens:
            return None

        if not self.current_token:
            raise AoPError("Unexpected end of expression.")

        left = self.atom()

        while self.current_token and self.current_token.kind == 'OPERATOR':
            op_info = OPERATORS.get(self.current_token.value)
            if not op_info or op_info['precedence'] < precedence:
                break

            op_token = self.current_token
            self.advance()

            if op_info['associativity'] == 'right':
                right = self.parse(op_info['precedence'])
            else:
                right = self.parse(op_info['precedence'] + 1)

            if right is None:
                raise SyntaxError("Incomplete expression: missing right operand")
            left = BinaryOpNode(left, op_token, right)

        return left

    def atom(self):
        token = self.current_token
        if not token:
            raise SyntaxError("Unexpected end of expression")

        if token.kind == 'AOP_LITERAL':
            from .aop_ast import AopLiteralNode
            self.advance()
            return AopLiteralNode(token)
        elif token.value == '(':
            self.advance()
            node = self.parse(0)
            if node is None:
                raise SyntaxError("Empty parentheses")
            if not self.current_token or self.current_token.value != ')':
                raise SyntaxError("Mismatched parentheses")
            self.advance()
            return node
        elif token.value in ('-', '+'):
            # This handles unary + and -
            self.advance()
            # Use a high precedence for the operand of a unary operator
            operand = self.parse(10)
            return UnaryOpNode(token, operand)

        raise SyntaxError(f"Unexpected token: {token}")
