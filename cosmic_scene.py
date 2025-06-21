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
                    self.update_node_dependencies(item)
                    self.removeItem(item)
            return
        super().keyPressEvent(event)

    def update_and_propagate(self, start_node):
        updated_in_this_run = set()
        def run_update(node_to_update):
            if node_to_update in updated_in_this_run: return
            updated_in_this_run.add(node_to_update)

            # 1. Get the current clean expression from the node
            current_full_text = node_to_update.toPlainText()
            current_clean_expr = current_full_text.partition('→')[0].strip()
            node_to_update.expression_str = current_clean_expr # Update the node's internal state

            if not current_clean_expr:
                node_to_update.set_display("", False)
                return

            # 2. Update dependencies and determine if this node defines a variable
            # This call will set node_to_update.defined_variable if applicable
            self.update_node_dependencies(node_to_update)

            expr_for_evaluation: str
            primary_var_name_for_node = node_to_update.defined_variable

            if primary_var_name_for_node: # If update_node_dependencies found a $var = ... pattern
                # The expression to get the value for the variable is the RHS of the first line
                # Note: update_node_dependencies looks at the whole expression_str for the "$var ="
                # For simplicity, we assume the RHS for the primary var is everything after the first '='
                # This might need refinement if a node defines $X = script_line1 \n script_line2
                # where script_line2 is the actual value for $X.
                # Current evaluate_script returns the value of the *last* line of its input.
                expr_for_evaluation = node_to_update.expression_str.partition('=')[2].strip()
            else:
                # No primary assignment, evaluate the whole text
                expr_for_evaluation = node_to_update.expression_str

            # 3. Handle incomplete expressions (for the part being evaluated)
            # Check the actual content that would be evaluated
            content_to_check_for_incomplete = expr_for_evaluation
            if primary_var_name_for_node: # If it's an assignment, check the RHS
                content_to_check_for_incomplete = node_to_update.expression_str.partition('=')[2].strip()

            if any(content_to_check_for_incomplete.endswith(op) for op in ['+', '-', '*', '/', '^', '**']):
                node_to_update.set_display("", False)
                return

            # 4. Handle special commands
            # A command is only on the first line. Subsequent lines are arguments or part of a script.
            first_line_of_expr = expr_for_evaluation.split('\n', 1)[0].strip()

            if first_line_of_expr.startswith("/"):
                is_command = True
                command_output = ""
                is_error_output = False
                # Parse the command from the first line only
                command_parts = first_line_of_expr.split(maxsplit=1)
                cmd = command_parts[0].lower() # Command is case-insensitive

                # Arguments for the command can be from the first line or subsequent lines
                first_line_args_str = command_parts[1].strip() if len(command_parts) > 1 else ""

                # For commands that can take multi-line arguments (like /explain <expr>)
                # The full expr_for_evaluation is relevant if no args on first line for such commands
                args = [a.strip() for a in first_line_args_str.split()] if first_line_args_str else []

                if cmd in ("/vars", "/variables"):
                    var_list_str = "Variables:\n"
                    if self.calculator.variables:
                        for var_name, aop_value in sorted(self.calculator.variables.items()):
                            val_str_direct = self.calculator.format_aop_value(aop_value, OutputFormatMode.AUTO, 10)
                            var_list_str += f"  {var_name} = {val_str_direct}\n"
                    else:
                        var_list_str += "  (none defined)"
                    command_output = var_list_str.strip()

                elif cmd in ("/help", "/?"):
                    command_output = "Available commands:\n"
                    command_output += "  /vars or /variables - Show variables\n"
                    command_output += "  /base - Show current base\n"
                    command_output += "  /setbase <num> - Set calculator base\n"
                    command_output += "  /constants - List #constants\n"
                    command_output += "  /letters or /aopabet - List AoP letter mappings\n"
                    command_output += "  /clearvars - Clear all user variables\n"
                    command_output += "  /delvar <varname> - Delete a specific variable\n"
                    command_output += "  /reset - Reset calculator state\n"
                    command_output += "  /rpn <expr> - Show RPN for expression\n"
                    command_output += "  /help or /? - Show this help\n"

                elif cmd == "/base":
                    command_output = f"Current base: {self.calculator.base}"

                elif cmd == "/setbase":
                    if args and args[0].isdigit():
                        window = self.views()[0].window()
                        if isinstance(window, CosmicScratchpadWindow):
                            window.trigger_base_change_and_full_recalc(args[0], command_node=node_to_update)
                        else:
                            command_output = "Error: Could not trigger base update via window."
                            is_error_output = True
                    else:
                        command_output = "Error: Usage /setbase <number>"
                        is_error_output = True
                    if command_output:
                        node_to_update.set_display(command_output, is_error_output)
                    return  # Command processed

                elif cmd == "/constants":
                    known_constants = ["#pi", "#e", "#phi", "#tau", "#sqrt2", "#j", "#sqrt3", "#ln2"]
                    command_output = "Predefined Constants:\n"
                    for const_name in known_constants:
                        try:
                            aop_val = get_term_value(const_name, {}, 'CONSTANT_LITERAL')
                            val_str = self.calculator.format_aop_value(aop_val, OutputFormatMode.AUTO, 10)
                            command_output += f"  {const_name} = {val_str}\n"
                        except ValueError:
                            command_output += f"  {const_name} = (Error resolving)\n"
                    command_output = command_output.strip()

                elif cmd in ("/letters", "/aopabet"):
                    command_output = "AoP Letter Mapping (Current Base):\n"
                    sorted_letters = sorted(LETTER_TO_EXPONENT_MAP.items(), key=lambda item: item[1])
                    for letter, exp in sorted_letters:
                        command_output += f"  {letter}: base^{exp}\n"
                    command_output = command_output.strip()

                elif cmd == "/clearvars":
                    self.calculator.variables.clear()
                    command_output = "All user variables cleared."
                    # Re-evaluate nodes to show errors for undefined variables
                    for item in self.items():
                        if isinstance(item, CalculationNode) and item != node_to_update:
                            item.update_node()

                elif cmd in ("/delvar", "/undef"):
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
                                    if dependent_node != node_to_update:
                                        run_update(dependent_node)
                        else:
                            command_output = f"Error: Variable {var_name} not found."
                            is_error_output = True
                    else:
                        command_output = "Error: Usage /delvar <variable_name>"
                        is_error_output = True

                elif cmd == "/reset":
                    self.calculator = AoP_Calculator(base=10, load_default_vars=True)
                    self.node_definitions = {}
                    self.dependencies = {}
                    window = self.views()[0].window()
                    if isinstance(window, CosmicScratchpadWindow):
                        window.base_input.setText("10")
                        window.trigger_base_change_and_full_recalc("10", command_node=None)
                    command_output = "Calculator state reset. Base set to 10. Variables cleared."
                    # Re-evaluate all nodes
                    for item in self.items():
                        if isinstance(item, CalculationNode) and item != node_to_update:
                            item.update_node()

                elif cmd == "/rpn":
                    expr_for_rpn = first_line_args_str.strip()
                    if expr_for_rpn:
                        try:
                            rpn_tokens = getattr(self.calculator, '_rpn_from_expression')(expr_for_rpn)
                            rpn_str = ", ".join([f"Token({t.kind},'{t.value}')" for t in rpn_tokens])
                            command_output = f"RPN for '{expr_for_rpn}':\n  [{rpn_str}]"
                        except Exception as e:
                            command_output = f"Error generating RPN: {e}"
                            is_error_output = True
                    else:
                        command_output = "Error: Usage /rpn <expression>"
                        is_error_output = True
                    node_to_update.set_display(command_output, is_error_output)
                    return  # Command processed

                elif cmd == "/explain":
                    # Display "thinking" message only if we are actually going to call AI
                    # The actual call to get_explanation might block, consider threading for long calls.
                    # For now, the GUI will freeze during the AI call.
                    ai_target_expr_str: str | None = None
                    ai_target_result_str: str | None = None

                    # Check for subcommands like 'last', 'model', 'help' on the first line
                    if first_line_args_str.lower() == "last":
                        # Logic for /explain last
                        if self.last_evaluated_calc_node and self.last_evaluated_calc_node.scene:
                            ai_target_expr_str = self.last_evaluated_calc_node.expression_str
                            if ai_target_expr_str:
                                temp_calc = AoP_Calculator(base=self.calculator.base, load_default_vars=False)
                                temp_calc.variables = self.calculator.variables.copy()
                                ai_target_result_str = temp_calc.evaluate_expression(ai_target_expr_str, OutputFormatMode.AUTO, 10)
                                if ai_target_result_str.startswith("Error:"): ai_target_result_str = None
                        else:
                            command_output = "Error: No previous calculation to explain."
                            is_error_output = True
                    elif first_line_args_str.lower().startswith("model"):
                        model_args = first_line_args_str.split(maxsplit=1)
                        if len(model_args) > 1:
                            self.current_ai_model = model_args[1]
                            command_output = f"AI model set to: {self.current_ai_model}"
                        else:
                            command_output = f"Error: Usage /explain model <name>. Current: {self.current_ai_model}"
                            is_error_output = True
                    elif first_line_args_str.lower() == "help":
                        command_output = "/explain [expr] | last | model <name> | help"
                        is_error_output = False
                    elif first_line_args_str: # /explain <expr_on_first_line>
                        ai_target_expr_str = first_line_args_str
                    else: # /explain (no args on first line)
                        # Check if there are subsequent lines in expr_for_evaluation
                        remaining_lines = expr_for_evaluation.split('\n', 1)
                        if len(remaining_lines) > 1 and remaining_lines[1].strip():
                            ai_target_expr_str = remaining_lines[1].strip() # Use rest of the node as expression
                        elif self.last_evaluated_calc_node and self.last_evaluated_calc_node.scene: # Fallback to last node
                            ai_target_expr_str = self.last_evaluated_calc_node.expression_str
                            if ai_target_expr_str: # Re-evaluate to get result for explanation
                                temp_calc = AoP_Calculator(base=self.calculator.base, load_default_vars=False)
                                temp_calc.variables = self.calculator.variables.copy()
                                ai_target_result_str = temp_calc.evaluate_expression(ai_target_expr_str, OutputFormatMode.AUTO, 10)
                                if ai_target_result_str.startswith("Error:"): ai_target_result_str = None
                        else: # No expression provided and no last node
                            command_output = "Usage: /explain <expression> or /explain last"
                            is_error_output = True

                    # If we have an expression to explain, but haven't gotten its result yet
                    if ai_target_expr_str and not ai_target_result_str and not command_output:
                        # Display "thinking" before the potentially blocking call
                        node_to_update.set_display("🤖 AI is thinking...", False, is_command_output=True)
                        temp_calc = AoP_Calculator(base=self.calculator.base, load_default_vars=False)
                        temp_calc.variables = self.calculator.variables.copy()
                        ai_target_result_str = temp_calc.evaluate_expression(ai_target_expr_str, OutputFormatMode.AUTO, 10)
                        if ai_target_result_str.startswith("Error:"):
                            command_output = f"Error evaluating for explanation: {ai_target_result_str}"
                            is_error_output = True
                            ai_target_result_str = None

                    if ai_target_expr_str and ai_target_result_str: # If we have both, get explanation
                        if not command_output: # Ensure "thinking" message is shown if not already set
                            # This might overwrite the "thinking" message if already set, which is fine
                            node_to_update.set_display("🤖 AI is thinking...", False, is_command_output=True)

                        explanation = get_explanation(ai_target_expr_str, ai_target_result_str, self.calculator.base, self.current_ai_model)
                        command_output = explanation
                        is_error_output = explanation.startswith("Error:")
                    elif not command_output: # Default error if nothing to explain was found
                        command_output = "Error: No expression provided or found to explain."
                        is_error_output = True

                    node_to_update.set_display(command_output, is_error_output, is_command_output=True)
                    return # Command processed

                else:
                    command_output = f"Error: Unknown command '{cmd}'. Type /help for a list."
                    is_error_output = True

                node_to_update.set_display(command_output, is_error_output)
                return  # Command processed, stop further evaluation

            # If not a command, ensure default wrapping for calculations
            else: # Not a command, it's a calculation
                doc_opt = QTextOption(node_to_update.document().defaultTextOption())
                if node_to_update.textWidth() < 1: # Not user-resized
                    doc_opt.setWrapMode(QTextOption.WrapMode.NoWrap)
                else: # User has resized it, so allow word wrap
                    doc_opt.setWrapMode(QTextOption.WrapMode.WordWrap)
                node_to_update.document().setDefaultTextOption(doc_opt)

            # 5. Regular script evaluation
            script_result_str = self.evaluate_script(expr_for_evaluation)
            script_is_error = script_result_str.startswith("Error:")

            # If it was a successful calculation (not a command that returned early, not an error), track it
            is_command = expr_for_evaluation.lstrip().startswith("/")
            if not is_command and not script_is_error:
                self.last_evaluated_calc_node = node_to_update  # Update last successful calc node

            # --- Convert 0/1 results from equality comparisons to True/False for display ---
            # This checks the expression that was actually sent to the backend for evaluation.
            # This is a display-only transformation.
            if "==" in expr_for_evaluation and not script_is_error: # Check original evaluated expression
                if script_result_str == "1":
                    script_result_str = "True"
                elif script_result_str == "0":
                    script_result_str = "False"

            if primary_var_name_for_node: # If this node was defining a variable
                if not script_is_error:
                    # The value for the primary variable is the result of the whole script (expr_for_evaluation)
                    try:
                        rpn_val = getattr(self.calculator, '_rpn_from_expression')(expr_for_evaluation)
                        val_obj = getattr(self.calculator, '_evaluate_rpn')(rpn_val)
                        self.calculator.variables[primary_var_name_for_node] = val_obj
                    except Exception as e_assign_val:
                        script_result_str = f"Error during final assignment to {primary_var_name_for_node}: {e_assign_val}"
                        script_is_error = True
                # If there was an error evaluating the RHS, or in assignment:
                if script_is_error and primary_var_name_for_node in self.calculator.variables:
                    del self.calculator.variables[primary_var_name_for_node] # Remove on error
            node_to_update.set_display(script_result_str, script_is_error)

            # 6. Propagation
            if primary_var_name_for_node and not script_is_error:
                if primary_var_name_for_node in self.dependencies:
                    for dependent_node in list(self.dependencies[primary_var_name_for_node]):
                        if dependent_node != node_to_update:
                            run_update(dependent_node)
            elif not primary_var_name_for_node and not script_is_error: # Pure expression changed, re-eval direct dependents if any
                # This case is more complex: what depends on a raw expression?
                # For now, only propagate if a variable defined by THIS node changed.
                pass

        start_node.expression_str = start_node.toPlainText().partition('→')[0].strip() # Ensure expression_str is fresh
        self.update_node_dependencies(start_node) # This sets start_node.defined_variable and its dependencies
        run_update(start_node)

    def update_node_dependencies(self, node):
        if node in self.node_definitions:
            old_var_name = self.node_definitions[node]
            if old_var_name in self.calculator.variables: del self.calculator.variables[old_var_name]
            self.node_definitions.pop(node)
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
        statements = [s.strip() for s in script_string.split('\n') if s.strip()]
        if not statements: return ""

        final_result_str = ""
        for statement_text in statements:
            current_line_is_assignment = False
            expr_to_eval_this_line = statement_text
            var_name_for_this_line = None

            match_assign = VARIABLE_REGEX.match(statement_text.lstrip())
            if match_assign:
                eq_index = statement_text.find('=')
                if eq_index > 0 and statement_text[eq_index-1] not in ['<', '>', '!'] and \
                   (eq_index + 1 >= len(statement_text) or statement_text[eq_index+1] != '='):
                    var_name_for_this_line = statement_text[:eq_index].strip()
                    if VARIABLE_REGEX.fullmatch(var_name_for_this_line):
                        current_line_is_assignment = True
                        expr_to_eval_this_line = statement_text[eq_index+1:].strip()
                    else:
                        final_result_str = f"Error: Invalid variable name '{var_name_for_this_line}'"
                        break

            if not expr_to_eval_this_line and current_line_is_assignment:
                final_result_str = "Error: Incomplete assignment"
                break

            line_result_val_str = self.calculator.evaluate_expression(
                expression=expr_to_eval_this_line,
                mode=OutputFormatMode.AUTO,
                precision=10
            )
            final_result_str = line_result_val_str

            if line_result_val_str.startswith("Error:"):
                if current_line_is_assignment and var_name_for_this_line in self.calculator.variables:
                    del self.calculator.variables[var_name_for_this_line]
                break

            if current_line_is_assignment and var_name_for_this_line:
                try:
                    rpn = getattr(self.calculator, '_rpn_from_expression')(expr_to_eval_this_line)
                    val_obj = getattr(self.calculator, '_evaluate_rpn')(rpn)
                    self.calculator.variables[var_name_for_this_line] = val_obj
                except Exception as e:
                    final_result_str = f"Error assigning to {var_name_for_this_line}: {e}"
                    if var_name_for_this_line in self.calculator.variables:
                        del self.calculator.variables[var_name_for_this_line]
                    break
        return final_result_str
