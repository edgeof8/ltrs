# cosmic_scene.py
import typing
import re
from PySide6.QtWidgets import QGraphicsScene, QToolBar, QApplication
from PySide6.QtGui import QPainterPath, QTextOption
from PySide6.QtCore import Qt
from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.definitions import OutputFormatMode, LETTER_TO_EXPONENT_MAP
from aopl_python_impl.aop_term_handler import get_term_value
from aopl_python_impl.aop_ai_explainer import get_explanation, DEFAULT_MODEL as DEFAULT_AI_MODEL
from gui_items import CalculationNode, LineItem, TextNoteItem, PenStrokeItem
from config import DrawingToolMode, VARIABLE_REGEX

if typing.TYPE_CHECKING:
    from main import CosmicScratchpadWindow

class CosmicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calculator = AoP_Calculator(base=10, load_default_vars=True)
        self.node_definitions = {}
        self.dependencies = {}
        self.window: 'CosmicScratchpadWindow | None' = None
        self.drawing_toolbar: 'QToolBar | None' = None
        self.current_drawing_tool: DrawingToolMode = DrawingToolMode.CALCULATE
        self.current_line_item = None
        self.current_pen_stroke = None
        self.last_pen_point = None
        self.last_evaluated_calc_node: CalculationNode | None = None
        self.current_ai_model: str = DEFAULT_AI_MODEL

        # Command handler dispatcher
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
            "/rpn": self._handle_rpn,
            "/explain": self._handle_explain
        }

    # --- COMMAND HANDLERS START ---

    def _handle_vars(self, context, node):
        var_list_str = "Variables:\n"
        if self.calculator.variables:
            for var_name, aop_value in sorted(self.calculator.variables.items()):
                val_str_direct = self.calculator.format_aop_value(aop_value, OutputFormatMode.AUTO, 10)
                var_list_str += f"  {var_name} = {val_str_direct}\n"
        else:
            var_list_str += "  (none defined)"
        command_output = var_list_str.strip()
        node.set_display(command_output, False, is_command_output=True)

    def _handle_help(self, context, node):
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

    def _handle_base(self, context, node):
        command_output = f"Current base: {self.calculator.base}"
        node.set_display(command_output, False)

    def _handle_setbase(self, context, node):
        args = context['first_line_args']
        if args and args[0].isdigit():
            window = self.views()[0].window()
            if isinstance(window, CosmicScratchpadWindow):
                # This call handles its own output displays
                window.trigger_base_change_and_full_recalc(args[0], command_node=node)
            else:
                node.set_display("Error: Could not trigger base update via window.", True)
        else:
            node.set_display("Error: Usage /setbase <number>", True)

    def _handle_constants(self, context, node):
        known_constants = ["#pi", "#e", "#phi", "#tau", "#sqrt2", "#j", "#sqrt3", "#ln2"]
        command_output = "Predefined Constants:\n"
        for const_name in known_constants:
            try:
                aop_val = get_term_value(const_name, {}, 'CONSTANT_LITERAL')
                val_str = self.calculator.format_aop_value(aop_val, OutputFormatMode.AUTO, 10)
                command_output += f"  {const_name} = {val_str}\n"
            except ValueError:
                command_output += f"  {const_name} = (Error resolving)\n"
        node.set_display(command_output.strip(), False, is_command_output=True)

    def _handle_letters(self, context, node):
        command_output = "AoP Letter Mapping (Current Base):\n"
        sorted_letters = sorted(LETTER_TO_EXPONENT_MAP.items(), key=lambda item: item[1])
        for letter, exp in sorted_letters:
            command_output += f"  {letter}: base^{exp}\n"
        node.set_display(command_output.strip(), False, is_command_output=True)

    def _handle_clearvars(self, context, node):
        self.calculator.variables.clear()
        node.set_display("All user variables cleared.", False)
        # Re-evaluate nodes to show errors for undefined variables
        for item in self.items():
            if isinstance(item, CalculationNode) and item != node:
                item.update_node()

    def _handle_delvar(self, context, node):
        args = context['first_line_args']
        if args:
            var_name = args[0]
            if not var_name.startswith("$"):
                var_name = f"${var_name}"
            if var_name in self.calculator.variables:
                del self.calculator.variables[var_name]
                command_output = f"{var_name} cleared."
                # Re-evaluate dependent nodes
                if var_name in self.dependencies:
                    for dependent_node in list(self.dependencies[var_name]):
                        if dependent_node != node:
                            self.update_and_propagate(dependent_node) # Use full update
                node.set_display(command_output, False)
            else:
                node.set_display(f"Error: Variable {var_name} not found.", True)
        else:
            node.set_display("Error: Usage /delvar <variable_name>", True)

    def _handle_reset(self, context, node):
        self.calculator = AoP_Calculator(base=10, load_default_vars=True)
        self.node_definitions = {}
        self.dependencies = {}
        window = self.views()[0].window()
        if isinstance(window, CosmicScratchpadWindow):
            window.base_input.setText("10")
            window.trigger_base_change_and_full_recalc("10", command_node=None)
        command_output = "Calculator state reset. Base set to 10. Variables cleared."
        node.set_display(command_output, False)
        for item in self.items():
            if isinstance(item, CalculationNode) and item != node:
                item.update_node()

    def _handle_rpn(self, context, node):
        expr_for_rpn = context['first_line_str']
        if expr_for_rpn:
            try:
                rpn_tokens = getattr(self.calculator, '_rpn_from_expression')(expr_for_rpn)
                rpn_str = ", ".join([f"Token({t.kind},'{t.value}')" for t in rpn_tokens])
                command_output = f"RPN for '{expr_for_rpn}':\n  [{rpn_str}]"
                is_error = False
            except Exception as e:
                command_output = f"Error generating RPN: {e}"
                is_error = True
        else:
            command_output = "Error: Usage /rpn <expression>"
            is_error = True
        node.set_display(command_output, is_error, is_command_output=True)

    def _handle_explain(self, context, node):
        first_line_str = context['first_line_str']
        full_expr = context['full_expr']
        command_output = ""
        is_error_output = False
        ai_target_expr_str = None
        ai_target_result_str = None

        if first_line_str.lower() == "last":
            if self.last_evaluated_calc_node and self.last_evaluated_calc_node.scene:
                ai_target_expr_str = self.last_evaluated_calc_node.expression_str
            else:
                command_output = "Error: No previous calculation to explain."
                is_error_output = True
        elif first_line_str.lower().startswith("model"):
            model_args = first_line_str.split(maxsplit=1)
            if len(model_args) > 1:
                self.current_ai_model = model_args[1]
                command_output = f"AI model set to: {self.current_ai_model}"
            else:
                command_output = f"Error: Usage /explain model <name>. Current: {self.current_ai_model}"
                is_error_output = True
        elif first_line_str: # /explain <expr>
            ai_target_expr_str = first_line_str
        else: # /explain on its own line
            remaining_lines = full_expr.split('\n', 1)
            if len(remaining_lines) > 1 and remaining_lines[1].strip():
                ai_target_expr_str = remaining_lines[1].strip()
            else:
                command_output = "Usage: /explain <expression> or /explain last"
                is_error_output = True

        if ai_target_expr_str and not command_output:
            node.set_display("🤖 AI is thinking...", False, is_command_output=True)
            QApplication.processEvents() # Allow GUI to update
            temp_calc = AoP_Calculator(base=self.calculator.base, load_default_vars=False)
            temp_calc.variables = self.calculator.variables.copy()
            ai_target_result_str = temp_calc.evaluate_expression(ai_target_expr_str, OutputFormatMode.AUTO, 10)
            if ai_target_result_str.startswith("Error:"):
                command_output = f"Error evaluating for explanation: {ai_target_result_str}"
                is_error_output = True
            else:
                explanation = get_explanation(ai_target_expr_str, ai_target_result_str, self.calculator.base, self.current_ai_model)
                command_output = explanation
                is_error_output = explanation.startswith("Error:")

        node.set_display(command_output, is_error_output, is_command_output=True)

    # --- COMMAND HANDLERS END ---


    def mousePressEvent(self, event):
        # Janitorial sweep for empty CalculationNodes (only in calc mode)
        if self.current_drawing_tool == DrawingToolMode.CALCULATE:
            for item in list(self.items()):
                if isinstance(item, CalculationNode) and not item.hasFocus() and not item.toPlainText().strip():
                    self.removeItem(item)

        item_at_click = self.itemAt(event.scenePos(), self.views()[0].transform())

        if self.current_drawing_tool == DrawingToolMode.CALCULATE:
            if item_at_click:
                super().mousePressEvent(event)
                return
            # Clicked on empty background in Calculate mode
            pos = event.scenePos()
            new_node = CalculationNode(self, self.calculator)
            self.addItem(new_node)
            new_node.setPos(pos)
            new_node.setFocus()

        elif self.current_drawing_tool == DrawingToolMode.LINE:
            self.current_line_item = LineItem(event.scenePos().x(), event.scenePos().y(),
                                              event.scenePos().x(), event.scenePos().y())
            self.addItem(self.current_line_item)

        elif self.current_drawing_tool == DrawingToolMode.TEXT_NOTE:
            if item_at_click and isinstance(item_at_click, TextNoteItem):
                super().mousePressEvent(event)
                return
            # Create new text note on empty space
            pos = event.scenePos()
            new_text_note = TextNoteItem("")
            self.addItem(new_text_note)
            new_text_note.setPos(pos)
            new_text_note.setFocus()

        elif self.current_drawing_tool == DrawingToolMode.PEN:
            self.current_pen_stroke = PenStrokeItem()
            self.addItem(self.current_pen_stroke)
            path = QPainterPath()
            path.moveTo(event.scenePos())
            self.current_pen_stroke.setPath(path)
            self.last_pen_point = event.scenePos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.current_drawing_tool == DrawingToolMode.LINE and self.current_line_item:
            line = self.current_line_item.line()
            line.setP2(event.scenePos())
            self.current_line_item.setLine(line)
            event.accept()
            return

        elif self.current_drawing_tool == DrawingToolMode.PEN and self.current_pen_stroke and self.last_pen_point:
            path = self.current_pen_stroke.path()
            path.lineTo(event.scenePos())
            self.current_pen_stroke.setPath(path)
            self.last_pen_point = event.scenePos()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_drawing_tool == DrawingToolMode.LINE and self.current_line_item:
            if self.current_line_item.line().length() < 5:
                self.removeItem(self.current_line_item)
            self.current_line_item = None

        elif self.current_drawing_tool == DrawingToolMode.PEN and self.current_pen_stroke:
            if self.current_pen_stroke.path().isEmpty() or self.current_pen_stroke.path().length() < 2:
                self.removeItem(self.current_pen_stroke)
            self.current_pen_stroke = None
            self.last_pen_point = None

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                if isinstance(item, CalculationNode):
                    # Find any nodes that depend on a variable this node defines
                    if item.defined_variable and item.defined_variable in self.dependencies:
                        dependents = list(self.dependencies[item.defined_variable])
                        for dep_node in dependents:
                            dep_node.update_node() # Re-evaluate to show error
                    # Remove the variable from the calculator and our tracking
                    if item.defined_variable in self.calculator.variables:
                        del self.calculator.variables[item.defined_variable]
                    if item in self.node_definitions:
                        del self.node_definitions[item]

                self.removeItem(item)
            return
        super().keyPressEvent(event)

    def update_and_propagate(self, start_node, propagate: bool = True):
        # The expression_str is already set by the node's event handlers.
        # We just need to use it.

        # 1. Get the expression from the node's state
        expr_for_evaluation = start_node.expression_str

        if not expr_for_evaluation:
            start_node.set_display("", False)
            return

        # 2. Update dependencies and determine if this node defines a variable
        self.update_node_dependencies(start_node)
        primary_var_name_for_node = start_node.defined_variable

        # 3. Handle special commands
        first_line_of_expr = expr_for_evaluation.split('\n', 1)[0].strip()
        if first_line_of_expr.startswith("/"):
            command_parts = first_line_of_expr.split(maxsplit=1)
            cmd = command_parts[0].lower()

            handler = self.command_handlers.get(cmd)
            if handler:
                context = {
                    'full_expr': expr_for_evaluation,
                    'first_line_args': command_parts[1].split() if len(command_parts) > 1 else [],
                    'first_line_str': command_parts[1] if len(command_parts) > 1 else ""
                }
                handler(context, start_node)
            else:
                start_node.set_display(f"Error: Unknown command '{cmd}'.", True)
            return # Commands do not propagate

        # 4. Regular script evaluation
        script_result_str = self.evaluate_script(expr_for_evaluation)
        script_is_error = script_result_str.startswith("Error:")

        if not script_is_error:
            self.last_evaluated_calc_node = start_node

        if "==" in expr_for_evaluation and not script_is_error:
            if script_result_str == "1": script_result_str = "True"
            elif script_result_str == "0": script_result_str = "False"

        if primary_var_name_for_node:
            if script_is_error and primary_var_name_for_node in self.calculator.variables:
                del self.calculator.variables[primary_var_name_for_node]

        start_node.set_display(script_result_str, script_is_error)

        # 5. Propagation (only if requested)
        if propagate and primary_var_name_for_node and not script_is_error:
            if primary_var_name_for_node in self.dependencies:
                for dependent_node in list(self.dependencies[primary_var_name_for_node]):
                    if dependent_node != start_node:
                        self.update_and_propagate(dependent_node, propagate=True)

    def update_node_dependencies(self, node):
        if node in self.node_definitions:
            old_var_name = self.node_definitions.pop(node)
            if old_var_name in self.calculator.variables: del self.calculator.variables[old_var_name]

        if node.dependencies:
            for var in node.dependencies:
                if var in self.dependencies: self.dependencies[var].discard(node)

        match = re.match(r"^\s*(\$[a-zA-Z_]\w*)\s*=", node.expression_str)
        if match:
            node.defined_variable = match.group(1)
            self.node_definitions[node] = node.defined_variable
        else:
            node.defined_variable = None

        node.dependencies = set(VARIABLE_REGEX.findall(node.expression_str))
        for var in node.dependencies:
            var_name = f"${var}"
            if var_name not in self.dependencies: self.dependencies[var_name] = set()
            self.dependencies[var_name].add(node)

    def evaluate_script(self, script_string: str) -> str:
        """
        Evaluates a multi-line script, isolating its execution state.
        Variables are only committed to the main calculator if the entire script succeeds.
        """
        statements = [s.strip() for s in script_string.split('\n') if s.strip()]
        if not statements:
            return ""

        # Create a temporary, isolated state for the script's execution
        temp_calculator = AoP_Calculator(base=self.calculator.base, load_default_vars=False)
        temp_calculator.variables = self.calculator.variables.copy()

        final_result_str = ""
        for statement_text in statements:
            try:
                # Use the main calculator's evaluate_expression, but with the temp state
                result_str = temp_calculator.evaluate_expression(
                    expression=statement_text,
                    mode=OutputFormatMode.AUTO,
                    precision=10
                )
                if result_str.startswith("Error:"):
                    return result_str  # Abort on the first error

                final_result_str = result_str # The result of the script is the result of the last line

            except Exception as e:
                # This catches deeper errors within the evaluation logic
                return f"Error: {type(e).__name__}: {e}"

        # If we got here, the entire script ran without errors.
        # Commit the changes from the temporary state to the main calculator.
        self.calculator.variables = temp_calculator.variables
        return final_result_str
