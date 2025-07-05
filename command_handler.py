# command_handler.py
from __future__ import annotations
from typing import TYPE_CHECKING
import re
from PySide6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QApplication
from PySide6.QtGui import QPen
from PySide6.QtCore import Qt
from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.constants import LETTER_TO_EXPONENT_MAP
from aopl_python_impl import aop_ai_explainer
from aopl_python_impl.aop_formatter import format_as_decimal_string
from gui_items.plot_node import PlotNode
from config import VARIABLE_REGEX
from cosmic_scene import CosmicScene

if TYPE_CHECKING:
    from main import CosmicScratchpadWindow
    from gui_items.calculation_node import CalculationNode

class CommandHandler:
    def __init__(self, scene: CosmicScene):
        self.scene = scene
        self.command_handlers = {
            "/vars": self._handle_vars,
            "/variables": self._handle_vars,
            "/help": self._handle_help,
            "/?": self._handle_help,
            "/base": self._handle_base,
            "/setbase": self._handle_setbase,
            "/constants": self._handle_constants,
            "/letters": self._handle_letters,
            "/aopabet": self._handle_letters,
            "/clearvars": self._handle_clearvars,
            "/delvar": self._handle_delvar,
            "/undef": self._handle_delvar,
            "/reset": self._handle_reset,
            "/explain": self._handle_explain,
            "/plot": self._handle_plot
        }

    def get_commands(self):
        return list(self.command_handlers.keys())

    def handle_command(self, command: str, context: dict, node):
        cmd = command.split()[0].lower() if command else ""
        handler = self.command_handlers.get(cmd)
        if handler:
            handler(context, node, self.scene.calculator)
        else:
            node.set_display(f"Error: Unknown command '{cmd}'.", True)

    def register_command(self, command: str, handler):
        if command in self.command_handlers:
            print(f"Warning: Overwriting existing command {command}")
        self.command_handlers[command] = handler

    # --- COMMAND HANDLERS START ---

    def _handle_vars(self, context, node, calculator=None):
        var_list_str = "Variables:\n"
        calc = calculator if calculator else self.scene.calculator
        if calc and calc.variables:
            for var_name, aop_value in sorted(calc.variables.items()):
                val_str_direct = format_as_decimal_string(aop_value)
                var_list_str += f"  {var_name} = {val_str_direct}\n"
        else:
            var_list_str += "  (none defined)"
        command_output = var_list_str.strip()
        node.set_display(command_output, False, is_command_output=True)

    def _handle_help(self, context, node, calculator=None):
        command_output = "Available commands:\n"
        command_output += "  /vars - Show variables\n"
        command_output += "  /base - Show current base\n"
        command_output += "  /setbase <num> - Set calculator base\n"
        command_output += "  /constants - List #constants\n"
        command_output += "  /letters - List AoP letter mappings\n"
        command_output += "  /delvar <var> - Delete a variable\n"
        command_output += "  /reset - Reset calculator state\n"
        command_output += "  /explain [expr|last] - AI explanation\n"
        command_output += "  /help - Show this help"
        node.set_display(command_output, False, is_command_output=True)

    def _handle_base(self, context, node, calculator=None):
        base = calculator.base if calculator else self.scene.calculator.base
        command_output = f"Current base: {base}"
        node.set_display(command_output, False)

    def _handle_setbase(self, context, node, calculator=None):
        args = context['first_line_args']
        if args and args[0].isdigit():
            window = self.scene.views()[0].window()
            if isinstance(window, CosmicScratchpadWindow):
                window.trigger_base_change_and_full_recalc(args[0], command_node=node)
            else:
                node.set_display("Error: Could not trigger base update via window.", True)
        else:
            node.set_display("Error: Usage /setbase <number>", True)

    def _handle_constants(self, context, node, calculator=None):
        known_constants = ["#pi", "#e", "#phi", "#tau", "#sqrt2", "#j", "#sqrt3", "#ln2"]
        command_output = "Predefined Constants:\n"
        calc_to_use = calculator if calculator else self.scene.calculator
        for const_name in known_constants:
            try:
                val_str, _ = calc_to_use.evaluate_expression(const_name, "num")
                command_output += f"  {const_name} = {val_str}\n"
            except Exception:
                command_output += f"  {const_name} = (Error resolving)\n"
        node.set_display(command_output.strip(), False, is_command_output=True)

    def _handle_letters(self, context, node, calculator=None):
        command_output = "AoP Letter Mapping (Current Base):\n"
        sorted_letters = sorted(LETTER_TO_EXPONENT_MAP.items(), key=lambda item: item[1])
        for letter, exp in sorted_letters:
            command_output += f"  {letter}: base^{exp}\n"
        node.set_display(command_output.strip(), False, is_command_output=True)

    def _handle_clearvars(self, context, node, calculator=None):
        calc = calculator if calculator else self.scene.calculator
        calc.variables.clear()
        node.set_display("All user variables cleared.", False)
        for item in self.scene.items():
            if isinstance(item, CalculationNode) and item != node:
                item.update_node_and_propagate()  # type: ignore

    def _handle_delvar(self, context, node, calculator=None):
        args = context['first_line_args']
        if args:
            var_name = args[0]
            if not var_name.startswith("$"):
                var_name = f"${var_name}"
            calc = calculator if calculator else self.scene.calculator
            if var_name in calc.variables:
                del calc.variables[var_name]
                command_output = f"{var_name} cleared."
                if var_name in self.scene.graph_manager.dependencies:
                    for dependent_node in list(self.scene.graph_manager.dependencies[var_name]):
                        if dependent_node != node:
                            self.scene.update_and_propagate(dependent_node)
                node.set_display(command_output, False)
            else:
                node.set_display(f"Error: Variable {var_name} not found.", True)
        else:
            node.set_display("Error: Usage /delvar <variable_name>", True)

    def _handle_reset(self, context, node, calculator=None):
        self.scene.calculator = AoP_Calculator(base=10)
        self.scene.graph_manager.clear()
        window = self.scene.views()[0].window()
        if isinstance(window, CosmicScratchpadWindow):
            window.base_input.setText("10")
            window.trigger_base_change_and_full_recalc("10", command_node=None)
        command_output = "Calculator state reset. Base set to 10. Variables cleared."
        node.set_display(command_output, False)
        for item in self.scene.items():
            if isinstance(item, CalculationNode) and item != node:
                item.update_node_and_propagate()  # type: ignore

    def _handle_explain(self, context, node, calculator=None):
        first_line_str = context['first_line_str']
        full_expr = context['full_expr']
        command_output = ""
        is_error_output = False
        ai_target_expr_str = None
        ai_target_result_str = None

        if first_line_str.lower() == "last":
            if self.scene.last_evaluated_calc_node and self.scene.last_evaluated_calc_node.scene:
                ai_target_expr_str = self.scene.last_evaluated_calc_node.expression_str
            else:
                command_output = "Error: No previous calculation to explain."
                is_error_output = True
        elif first_line_str.lower().startswith("model"):
            model_args = first_line_str.split(maxsplit=1)
            if len(model_args) > 1:
                self.scene.current_ai_model = model_args[1]
                command_output = f"AI model set to: {self.scene.current_ai_model}"
            else:
                command_output = f"Error: Usage /explain model <name>. Current: {self.scene.current_ai_model}"
                is_error_output = True
        elif first_line_str:
            ai_target_expr_str = first_line_str
        else:
            remaining_lines = full_expr.split('\n', 1)
            if len(remaining_lines) > 1 and remaining_lines[1].strip():
                ai_target_expr_str = remaining_lines[1].strip()
            else:
                command_output = "Usage: /explain <expression> or /explain last"
                is_error_output = True

        if ai_target_expr_str and not command_output:
            node.set_display("🤖 AI is thinking...", False, is_command_output=True)
            QApplication.processEvents()
            calc_to_use = calculator if calculator else self.scene.calculator
            temp_calc = AoP_Calculator(base=calc_to_use.base)
            temp_calc.variables = calc_to_use.variables.copy()
            ai_target_result_str, _ = temp_calc.evaluate_expression(ai_target_expr_str, "num")
            if ai_target_result_str.startswith("Error:"):
                command_output = f"Error evaluating for explanation: {ai_target_result_str}"
                is_error_output = True
            else:
                _, ast_for_explainer = temp_calc.evaluate_expression(ai_target_expr_str, "num")
                if ast_for_explainer is None:
                    command_output = "Error: Could not parse expression for AI explanation."
                    is_error_output = True
                else:
                    _, explanation = aop_ai_explainer.get_ai_explanation_and_session(ai_target_expr_str, ai_target_result_str, calc_to_use.base, ast_for_explainer)
                    if explanation is None:
                        command_output = "Error: AI explanation service failed."
                        is_error_output = True
                    else:
                        command_output = explanation
                        is_error_output = explanation.startswith("Error:")

        node.set_display(command_output, is_error_output, is_command_output=True)

    def _handle_plot(self, context, node, calculator=None):
        first_line_str = context['first_line_str']
        parts = first_line_str.split()
        expression = ""
        variable = ""
        start_val = "1"
        end_val = "100"
        steps = 200
        log_x = False
        log_y = False

        if len(parts) >= 5 and "for" in parts and "from" in parts and "to" in parts:
            for_idx = parts.index("for")
            from_idx = parts.index("from")
            to_idx = parts.index("to")
            if for_idx < from_idx < to_idx:
                expression = " ".join(parts[:for_idx])
                variable = parts[for_idx + 1]
                start_val = parts[from_idx + 1]
                end_val = parts[to_idx + 1]
        else:
            class PlotConfigDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Plot Configuration")
                    layout = QVBoxLayout(self)

                    expr_layout = QHBoxLayout()
                    expr_label = QLabel("Expression:")
                    self.expr_input = QLineEdit()
                    expr_layout.addWidget(expr_label)
                    expr_layout.addWidget(self.expr_input)
                    layout.addLayout(expr_layout)

                    var_layout = QHBoxLayout()
                    var_label = QLabel("Variable:")
                    self.var_input = QLineEdit()
                    var_layout.addWidget(var_label)
                    var_layout.addWidget(self.var_input)
                    layout.addLayout(var_layout)

                    start_layout = QHBoxLayout()
                    start_label = QLabel("Start Value:")
                    self.start_input = QLineEdit("1")
                    start_layout.addWidget(start_label)
                    start_layout.addWidget(self.start_input)
                    layout.addLayout(start_layout)

                    end_layout = QHBoxLayout()
                    end_label = QLabel("End Value:")
                    self.end_input = QLineEdit("100")
                    end_layout.addWidget(end_label)
                    end_layout.addWidget(self.end_input)
                    layout.addLayout(end_layout)

                    steps_layout = QHBoxLayout()
                    steps_label = QLabel("Steps:")
                    self.steps_input = QLineEdit("200")
                    steps_layout.addWidget(steps_label)
                    steps_layout.addWidget(self.steps_input)
                    layout.addLayout(steps_layout)

                    self.log_x_check = QCheckBox("Logarithmic X-axis")
                    self.log_y_check = QCheckBox("Logarithmic Y-axis")
                    layout.addWidget(self.log_x_check)
                    layout.addWidget(self.log_y_check)

                    button_layout = QHBoxLayout()
                    ok_button = QPushButton("OK")
                    cancel_button = QPushButton("Cancel")
                    ok_button.clicked.connect(self.accept)
                    cancel_button.clicked.connect(self.reject)
                    button_layout.addStretch()
                    button_layout.addWidget(ok_button)
                    button_layout.addWidget(cancel_button)
                    layout.addLayout(button_layout)

            dialog = PlotConfigDialog()
            if dialog.exec():
                expression = dialog.expr_input.text()
                variable = dialog.var_input.text()
                start_val = dialog.start_input.text()
                end_val = dialog.end_input.text()
                steps_str = dialog.steps_input.text()
                log_x = dialog.log_x_check.isChecked()
                log_y = dialog.log_y_check.isChecked()

                if not expression:
                    node.set_display("Error: No expression provided for plot.", True)
                    return
                if not variable:
                    node.set_display("Error: No variable provided for plot.", True)
                    return
                if not start_val:
                    node.set_display("Error: No start value provided for plot.", True)
                    return
                if not end_val:
                    node.set_display("Error: No end value provided for plot.", True)
                    return
                try:
                    steps = int(steps_str) if steps_str else 200
                except ValueError:
                    steps = 200
            else:
                node.set_display("Error: Plot configuration cancelled.", True)
                return

        if not variable.startswith("$"):
            variable = f"${variable}"

        calc_to_use = calculator if calculator else self.scene.calculator
        plot_node = PlotNode(self.scene, calc_to_use, expression, variable[1:], start_val, end_val, steps, log_x, log_y)
        self.scene.addItem(plot_node)
        plot_node.setPos(node.pos().x() + 50, node.pos().y() + 50)
        node.set_display(f"Plot created for {expression}", False)
        self.scene.graph_manager.update_dependencies_for_node(plot_node)

    # --- COMMAND HANDLERS END ---
