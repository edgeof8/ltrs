# aopl_python_impl/aop_parser.py
import logging, re
from typing import List
from .definitions import Token, AoPError, OPERATORS
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode

def tokenize_expression(expression: str) -> List[Token]:
    """
    A stateful tokenizer that understands the 'additive by default' grammar.
    It correctly tokenizes sequences like '2b3c' and 'abc' into separate terms.
    """
    from .definitions import TOKEN_REGEX
    tokens = []
    pos = 0
    while pos < len(expression):
        char = expression[pos]

        if char.isspace():
            pos += 1
            continue

        # Match standard operators and parentheses using regex
        match = TOKEN_REGEX.match(expression, pos)
        if match:
            kind = match.lastgroup
            value = match.group()
            if kind is not None:
                tokens.append(Token(kind, value, pos, match.end()))
                pos = match.end()
                continue

        # Match numbers (could be part of a term or standalone)
        if char.isdigit() or char == '.':
            num_str = ""
            start_pos = pos
            while pos < len(expression) and (expression[pos].isdigit() or expression[pos] == '.'):
                num_str += expression[pos]
                pos += 1

            # Look ahead to see if it's followed by a letter
            if pos < len(expression) and expression[pos].isalpha():
                # It's a coefficient for a letter, e.g., "2a"
                tokens.append(Token('TERM', num_str + expression[pos], start_pos, pos + 1))
                pos += 1 # Consume the letter
            else:
                # It's a standalone number
                tokens.append(Token('NUMBER', num_str, start_pos, pos))
            continue

        # Match single letters (which can form implicit terms)
        if char.isalpha():
            # A letter by itself is a term with a coefficient of 1
            tokens.append(Token('TERM', char, pos, pos + 1))
            pos += 1
            continue

        # If we get here, it's an unknown character
        raise SyntaxError(f"Unexpected character at position {pos}: {char}")

    # --- Phase 2: Insert Implicit Addition Operators ---
    # Iterate through the token stream and insert ADD operators where needed.
    final_tokens = []
    for i, token in enumerate(tokens):
        final_tokens.append(token)
        # If the current token is a TERM or a RPAREN, and the next token is a TERM or LPAREN, insert ADD
        if i + 1 < len(tokens):
            current_type = token.kind
            next_type = tokens[i+1].kind
            if (current_type in ('TERM', 'NUMBER', 'RPAREN')) and \
               (next_type in ('TERM', 'NUMBER', 'LPAREN')):
                final_tokens.append(Token('OPERATOR', '+', -1, -1)) # Position doesn't matter for implicit ops

    logging.debug(f"Tokens: {final_tokens}")
    return final_tokens

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
        if token.kind == 'TERM': self.advance(); return IdentifierNode(token) # Treat TERM as Identifier for now
        if token.kind == 'IDENTIFIER': self.advance(); return IdentifierNode(token)
        if token.value == '(':
            self.advance(); node = self.parse()
            if not self.current_token or self.current_token.value != ')':
                raise AoPError("Mismatched parentheses")
            self.advance()
            return node
        raise AoPError(f"Unexpected token: {token}")
