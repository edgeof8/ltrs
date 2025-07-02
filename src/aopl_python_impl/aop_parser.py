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

def group_aop_literals(tokens: List[Token]) -> List[Token]:
    if not tokens:
        return []

    grouped_tokens = []
    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.kind in ('TERM', 'NUMBER'):
            current_group = [token]
            j = i + 1
            while j < len(tokens) and tokens[j].kind in ('TERM', 'NUMBER'):
                current_group.append(tokens[j])
                j += 1

            if len(current_group) > 1:
                full_value = "".join(t.value for t in current_group)
                grouped_tokens.append(Token('AOP_LITERAL', full_value, token.start, current_group[-1].end))
            else:
                grouped_tokens.append(token)
            i = j
        else:
            grouped_tokens.append(token)
            i += 1
    return grouped_tokens

def tokenize_expression(expression: str) -> List[Token]:
    """A stateful tokenizer for the AoP grammar (additive by default)."""
    # This regex splits the string by operators/parentheses, keeping them as delimiters
    TOKEN_REGEX = re.compile(r"(\*\*|==|[+\-*/^()])")
    raw_parts = TOKEN_REGEX.split(expression)
    tokens = []
    pos = 0

    for part in raw_parts:
        part = part.strip()
        if not part:
            continue

        start_pos = expression.find(part, pos)
        end_pos = start_pos + len(part)
        pos = end_pos

        if part in "()":
            kind = 'LPAREN' if part == '(' else 'RPAREN'
            tokens.append(Token(kind, part, start_pos, end_pos))
        elif part in OPERATORS:
            tokens.append(Token('OPERATOR', part, start_pos, end_pos))
        else:
            # This part is a sequence of numbers and letters, e.g., "2b5c" or "abc"
            # We need to break it down into individual terms
            term_matches = re.finditer(r'([0-9\.]*[a-zA-Z])|([0-9\.]+)', part)
            for match in term_matches:
                term_value = match.group(0)
                term_start = start_pos + match.start()
                term_end = start_pos + match.end()
                if term_value.replace('.', '').isnumeric():
                    tokens.append(Token('NUMBER', term_value, term_start, term_end))
                else:
                    tokens.append(Token('TERM', term_value, term_start, term_end))

    # Group consecutive terms into a single literal
    grouped = group_aop_literals(tokens)

    # Insert implicit addition operators
    final_tokens = []
    for i, token in enumerate(grouped):
        final_tokens.append(token)
        if i + 1 < len(grouped):
            # If two literals/terms/numbers are next to each other, it's addition
            if grouped[i].kind in ('AOP_LITERAL', 'TERM', 'NUMBER', 'RPAREN') and \
               grouped[i+1].kind in ('AOP_LITERAL', 'TERM', 'NUMBER', 'LPAREN'):
                final_tokens.append(Token('OPERATOR', '+', -1, -1))

    logging.debug(f"Tokens: {final_tokens}")
    return final_tokens

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens; self.pos = -1; self.current_token = None
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self):
        return self.parse_expression()

    def parse_expression(self, precedence=0):
        left = self.atom()

        while self.current_token and self.current_token.kind == 'OPERATOR' and OPERATORS.get(self.current_token.value, {}).get('precedence', 0) > precedence:
            op = self.current_token
            self.advance()
            op_info = OPERATORS[op.value]
            next_precedence = op_info['precedence'] + (1 if op_info['associativity'] == 'left' else 0)
            right = self.parse_expression(next_precedence)
            left = BinaryOpNode(left, op, right)
        return left
        left = self.parse_power() # Go down to the next precedence level

        while self.current_token and self.current_token.value in ('*', '/'):
            op = self.current_token
            self.advance()
            right = self.parse_power()
            left = BinaryOpNode(left, op, right)

        return left

    def parse_power(self):
        left = self.atom()

        if self.current_token and self.current_token.value == '^':
            op = self.current_token
            self.advance()
            # Power is right-associative
            right = self.parse_power()
            return BinaryOpNode(left, op, right)

        return left

    def atom(self):
        if not self.current_token:
            raise SyntaxError("Unexpected end of expression")
        token = self.current_token
        if token.kind == 'AOP_LITERAL':
            self.advance()
            return AopLiteralNode(token)
        if token.kind == 'NUMBER':
            self.advance()
            return NumberNode(token)
        if token.kind == 'TERM':
            self.advance()
            return IdentifierNode(token)
        if token.value == '(':
            self.advance()
            node = self.parse()  # Start parsing from the top level again
            if not self.current_token or self.current_token.value != ')':
                raise SyntaxError("Mismatched parentheses")
            self.advance()  # Consume ')'
            return node

        raise SyntaxError(f"Unexpected token: {token}")
