# aopl_python_impl/aop_prompt_builder.py
#
# This module defines the `PromptBuilderVisitor`, a class that implements the
# visitor design pattern to traverse an AST. Its purpose is to walk a given
# expression's AST and construct a detailed, structured, step-by-step analysis
# of the calculation. This analysis is then used as a system prompt for the AI
# explainer, ensuring a highly accurate and relevant explanation.

from .aop_ast import ASTNode, BinaryOpNode, AopLiteralNode, IdentifierNode, UnaryOpNode, VariableNode
from .aop_value import AoPValue

class PromptBuilderVisitor:
    """
    Traverses the AST to build a structured, detailed prompt for the AI.
    """
    def __init__(self, base: int):
        self.base = base
        self.analysis_blocks = []
        self.node_counter = 0

    def build_prompt(self, ast: ASTNode) -> str:
        """Builds the master system prompt for the instructor AI."""
        # Start with a comprehensive overview of the AoP system.
        system_overview = f"""
# SYSTEM OVERVIEW: Alphabet of Powers (AoP) Calculator

You are a precise, technical writer for the AoP calculator. Your task is to synthesize the provided step-by-step analysis of a calculation into a clear, human-readable explanation.

## Core Notation (Current Base: {self.base})
- **Letters as Exponents:** Letters represent powers of the base. `a`=1, `b`=2, ..., `y`=25, `A`=26, ..., `Y`=50, `Z`=100.
- **Literals as Polynomials:** An AoP literal is a sum of its terms. It is NOT a place-value number.
  - **Example:** `2c4a` is parsed as `(2 * base^3) + (4 * base^1)`.
- **Variables:** Variables are denoted with a `$` prefix, e.g., `$x`.
"""
        # Traverse the AST to generate the analysis blocks for this specific calculation.
        self.visit(ast)
        # Reverse the blocks so the prompt shows the steps from inner-most to outer-most.
        self.analysis_blocks.reverse()
        analysis_str = "\n".join(self.analysis_blocks)

        # The final prompt combines the overview with the specific analysis.
        final_prompt = f"""
{system_overview}

# CALCULATION ANALYSIS
This is a step-by-step, inside-out breakdown of the expression.

{analysis_str}

# YOUR TASK
Synthesize the above "CALCULATION ANALYSIS" into a polished, final explanation.
- Explain each step clearly using the provided information.
- Start with the decomposition of the base literals and work your way to the final operation.
- Be direct, technical, and omit all conversational fluff.
"""
        return final_prompt

    def visit(self, node: ASTNode) -> str:
        """Dispatcher method that calls the appropriate visit_* method."""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise NotImplementedError(f'No visit_{type(node).__name__} method')

    def visit_AopLiteralNode(self, node: AopLiteralNode) -> str:
        self.node_counter += 1
        node_id = f"LITERAL_VAL_{self.node_counter}"
        aop_val = AoPValue.from_literal(node.value, self.base)
        decomposition = aop_val.get_decomposition_str()
        numerical_value = aop_val.to_numerical()

        block = f"""---
### Step {self.node_counter}: Decompose Literal `{node.value}` -> {node_id}
- **Rule:** An AoP literal is parsed as a sum of its terms.
- **Decomposition for `{node.value}`:** `{decomposition}`
- **Numerical Value:** `{numerical_value}`
---"""
        self.analysis_blocks.append(block)
        return node_id

    def visit_VariableNode(self, node: VariableNode) -> str:
        self.node_counter += 1
        node_id = f"VAR_VAL_{self.node_counter}"
        block = f"""---
### Step {self.node_counter}: Reference Variable `{node.name}` -> {node_id}
- **Rule:** The value of the variable `{node.name}` is retrieved from memory.
---"""
        self.analysis_blocks.append(block)
        return node_id

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        operand_id = self.visit(node.right)
        self.node_counter += 1
        node_id = f"UNARY_OP_RESULT_{self.node_counter}"
        block = f"""---
### Step {self.node_counter}: Apply Unary Operator `{node.op.value}` -> {node_id}
- **Input:** `{operand_id}`
- **Rule:** The unary operator `{node.op.value}` is applied to its operand.
---"""
        self.analysis_blocks.append(block)
        return node_id

    def visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        left_id = self.visit(node.left)
        right_id = self.visit(node.right)
        self.node_counter += 1
        node_id = f"BINARY_OP_RESULT_{self.node_counter}"
        op = node.op.value

        if op in ('^', '**'):
            rule_desc = "A power operation is performed. If the base is a pure power of the calculation base (e.g., `a` which is `base^1`), this is a **Symbolic Power** operation where exponents are multiplied. Otherwise, it is a **Numerical Power** operation using the Multinomial Theorem."
        else:
            rule_desc = f"A standard arithmetic operation (`{op}`) is performed on the numerical values of the operands."

        block = f"""---
### Step {self.node_counter}: Apply Binary Operator `{op}` -> {node_id}
- **Left Operand:** From `{left_id}`
- **Right Operand:** From `{right_id}`
- **Rule:** {rule_desc}
---"""
        self.analysis_blocks.append(block)
        return node_id
