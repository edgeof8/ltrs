# evaluation_manager.py
from __future__ import annotations
from typing import TYPE_CHECKING
from aopl_python_impl.aop_calculator import AoP_Calculator
from PySide6.QtWidgets import QApplication
from gui_items.calculation_node import CalculationNode
from gui_items.plot_node import PlotNode

if TYPE_CHECKING:
    from cosmic_scene import CosmicScene

class EvaluationManager:
    def __init__(self, scene: 'CosmicScene'):
        self.scene = scene

    def process_node_update(self, start_node: 'CalculationNode | PlotNode', propagate: bool = True) -> None:
        """
        Processes the update of a node, evaluating its script or handling commands,
        updating its display, and propagating changes to dependent nodes.
        """
        # Get the expression from the node's state
        if isinstance(start_node, CalculationNode):
            expr_for_evaluation = start_node.expression_str
        else:  # PlotNode
            expr_for_evaluation = start_node.expression

        if not expr_for_evaluation:
            if isinstance(start_node, CalculationNode):
                start_node.set_display("", False)
            return

        # Handle special commands for CalculationNode
        if isinstance(start_node, CalculationNode):
            first_line_of_expr = expr_for_evaluation.split('\n', 1)[0].strip()
            if first_line_of_expr.startswith("/"):
                command_parts = first_line_of_expr.split(maxsplit=1)
                cmd = command_parts[0].lower()

                handler = self.scene.command_handlers.get(cmd)
                if handler:
                    context = {
                        'full_expr': expr_for_evaluation,
                        'first_line_args': command_parts[1].split() if len(command_parts) > 1 else [],
                        'first_line_str': command_parts[1] if len(command_parts) > 1 else ""
                    }
                    handler(context, start_node, self.scene.calculator)
                else:
                    start_node.set_display(f"Error: Unknown command '{cmd}'.", True)
                return  # Commands do not propagate

        # Regular script evaluation
        script_result_str = self.evaluate_script(expr_for_evaluation)
        script_is_error = script_result_str.startswith("Error:")

        if not script_is_error and isinstance(start_node, CalculationNode):
            self.scene.last_evaluated_calc_node = start_node

        if "==" in expr_for_evaluation and not script_is_error:
            if script_result_str == "1":
                script_result_str = "True"
            elif script_result_str == "0":
                script_result_str = "False"

        if hasattr(start_node, 'defined_variable') and start_node.defined_variable:
            if script_is_error and start_node.defined_variable in self.scene.calculator.variables:
                del self.scene.calculator.variables[start_node.defined_variable]

        if isinstance(start_node, CalculationNode):
            start_node.set_display(script_result_str, script_is_error)

        # Propagation (only if requested and for CalculationNode with defined variable)
        if propagate and hasattr(start_node, 'defined_variable') and start_node.defined_variable and not script_is_error:
            if start_node.defined_variable in self.scene.graph_manager.dependencies:
                for dependent_node in list(self.scene.graph_manager.dependencies[start_node.defined_variable]):
                    if dependent_node != start_node:
                        if isinstance(dependent_node, PlotNode):
                            dependent_node.redraw_plot()
                        else:
                            self.process_node_update(dependent_node, propagate=True)

    def evaluate_script(self, script_string: str) -> str:
        """
        Evaluates a multi-line script, isolating its execution state.
        Variables are only committed to the main calculator if the entire script succeeds.
        """
        statements = [s.strip() for s in script_string.split('\n') if s.strip()]
        if not statements:
            return ""

        # Create a temporary, isolated state for the script's execution
        temp_calculator = AoP_Calculator(base=self.scene.calculator.base)
        temp_calculator.variables = self.scene.calculator.variables.copy()

        final_result_str = ""
        for statement_text in statements:
            try:
                # Use the main calculator's evaluate_expression, but with the temp state
                result_str, _ = temp_calculator.evaluate_expression(
                    expression=statement_text,
                    mode="auto"
                )
                if result_str.startswith("Error:"):
                    return result_str  # Abort on the first error

                final_result_str = result_str  # The result of the script is the result of the last line

            except Exception as e:
                # This catches deeper errors within the evaluation logic
                return f"Error: {type(e).__name__}: {str(e)}"

        # If we got here, the entire script ran without errors.
        # Commit the changes from the temporary state to the main calculator.
        self.scene.calculator.variables = temp_calculator.variables
        return final_result_str
