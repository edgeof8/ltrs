# aopl_python_impl/aop_parser.py
#
# This module handles the first two stages of interpreting a user's expression:
# 1. Tokenizer: Scans the raw string and breaks it into a list of meaningful tokens
#    (e.g., literals, operators, variables).
# 2. Parser: Takes the list of tokens and constructs an Abstract Syntax Tree (AST).
import logging, re
from typing import List
from .definitions import Token, AoPError
from .constants import OPERATORS, TOKEN_REGEX
from .aop_ast import ASTNode, NumberNode, IdentifierNode, BinaryOpNode, UnaryOpNode, VariableNode

_DIGIT_GROUP_COMMA = re.compile(r"(?<=\d),(?=\d)")


def strip_digit_group_commas(text: str) -> str:
    """Remove commas that sit between digits (num-mode grouping on paste)."""
    return _DIGIT_GROUP_COMMA.sub("", text)


def tokenize_expression(expression: str) -> List[Token]:
    """
    A stateful tokenizer that understands the 'additive by default' grammar.
    It correctly tokenizes sequences like '2b3c' into a single AopLiteralNode.
    """
    # This regex identifies all tokens of interest.
    # - \$[a-zA-Z_][a-zA-Z0-9_]* : Finds variables, e.g., $x, $my_var
    # - \*\*                       : Finds power operator '**'
    # - ==?                        : Finds equality '==' and assignment '=' (Note: '=' is handled separately below)
    # - [+\-*/^()]                 : Finds single-character operators and parentheses
    expression = strip_digit_group_commas(expression)
    token_regex = re.compile(r"(\$[a-zA-Z_][a-zA-Z0-9_]*|\*\*|==?|[+\-*/^()])")
    raw_parts = [p.strip() for p in token_regex.split(expression) if p.strip()]
    tokens = []
    pos = 0
    for part in raw_parts:
        start_pos = expression.find(part, pos)
        end_pos = start_pos + len(part)
        pos = end_pos
        if part.startswith('$'):
            tokens.append(Token('VARIABLE', part, start_pos, end_pos))
        elif part in OPERATORS or part == '=':
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
            # Nested parse of a missing operand (e.g. trailing '=').
            if precedence > 0:
                return None
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
                # Trailing '=' is a calculator "equals" marker: evaluate the left-hand side.
                if op_token.value == '=':
                    break
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
        elif token.kind == 'VARIABLE':
            self.advance()
            return VariableNode(token)
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
