# evaluation_manager.py
from __future__ import annotations
from typing import TYPE_CHECKING
from .script_eval import run_isolated_script
from .gui_items.calculation_node import CalculationNode
from .gui_items.plot_node import PlotNode

if TYPE_CHECKING:
    from .cosmic_scene import CosmicScene

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

        if self.scene.graph_manager.has_cycle():
            if isinstance(start_node, CalculationNode):
                start_node.set_display("Error: Variable dependency cycle.", True)
            return

        mode = getattr(start_node, "output_mode", "num")
        script_result_str = self.evaluate_script(expr_for_evaluation, mode=mode)
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

    def evaluate_script(self, script_string: str, mode: str = "num") -> str:
        return run_isolated_script(self.scene.calculator, script_string, mode=mode)
