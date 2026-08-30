import unittest
from src.aopl_python_impl.aop_parser import tokenize_expression, Parser
from src.aopl_python_impl.aop_ast import AopLiteralNode, BinaryOpNode


class TestAoPParser(unittest.TestCase):
    def test_juxtaposed_letters_are_one_literal(self):
        tokens = tokenize_expression("ba")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].kind, "AOP_LITERAL")
        self.assertEqual(tokens[0].value, "ba")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, AopLiteralNode)
        self.assertEqual(ast.to_str(), "ba")

    def test_explicit_multiply_is_binary(self):
        ast = Parser(tokenize_expression("a*b")).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.op.value, "*")

    def test_power_is_right_associative(self):
        ast = Parser(tokenize_expression("a^b^c")).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.op.value, "^")
        self.assertIsInstance(ast.right, BinaryOpNode)
        self.assertEqual(ast.right.op.value, "^")

    def test_trailing_equals_drops_equals_marker(self):
        ast = Parser(tokenize_expression("a=")).parse()
        self.assertIsInstance(ast, AopLiteralNode)
        self.assertEqual(ast.to_str(), "a")

    def test_division_is_left_associative(self):
        ast = Parser(tokenize_expression("c/a/a")).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.op.value, "/")
        self.assertIsInstance(ast.left, BinaryOpNode)
        self.assertEqual(ast.left.op.value, "/")
