# cosmic_scene.py
import typing
import re
from PySide6.QtWidgets import QGraphicsScene, QToolBar
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import Qt
from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.definitions import OutputFormatMode, LETTER_TO_EXPONENT_MAP
from aopl_python_impl.aop_term_handler import get_term_value
from gui_items import CalculationNode, LineItem, TextNoteItem, PenStrokeItem
from config import DrawingToolMode, VARIABLE_REGEX

if typing.TYPE_CHECKING:
    from main import CosmicScratchpadWindow

class CosmicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calculator = AoP_Calculator(base=10)
        self.node_definitions = {}
        self.dependencies = {}
        self.window: 'CosmicScratchpadWindow | None' = None
        self.drawing_toolbar: 'QToolBar | None' = None
        self.current_drawing_tool: DrawingToolMode = DrawingToolMode.CALCULATE
        self.current_line_item = None
        self.current_pen_stroke = None
        self.last_pen_point = None

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

            full_text = node_to_update.toPlainText()
            clean_expr = full_text.partition('→')[0].strip()
            node_to_update.expression_str = clean_expr

            if not clean_expr:
                node_to_update.set_display("", False)
                return
            if any(clean_expr.endswith(op) for op in ['+', '-', '*', '/', '^', '**']):
                node_to_update.set_display("", False)
                return

            self.update_node_dependencies(node_to_update)

            expr_to_eval = clean_expr
            is_assignment = '=' in expr_to_eval
            if is_assignment:
                var_name, _, expr_to_eval_rhs = expr_to_eval.partition('=')
                var_name = var_name.strip()
                if not VARIABLE_REGEX.match(var_name):
                    msg = "Invalid variable name. Variables must start with a '$'."
                    node_to_update.set_display(msg, True)
                    return
                expr_to_eval = expr_to_eval_rhs.strip()

            # Command parsing
            if clean_expr.startswith("/"):
                is_command = True
                command_output = ""
                is_error_output = False
                parts = clean_expr.lower().split(maxsplit=1)
                cmd = parts[0]
                args_str = parts[1] if len(parts) > 1 else ""
                args = [a.strip() for a in args_str.split()] if args_str else []

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
                    self.calculator = AoP_Calculator(base=10)
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
                    expr_for_rpn = args_str.strip()
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

                else:
                    command_output = f"Error: Unknown command '{cmd}'. Type /help for a list."
                    is_error_output = True

                node_to_update.set_display(command_output, is_error_output)
                return  # Command processed, stop further evaluation

            script_result_str = self.evaluate_script(expr_to_eval)
            script_is_error = script_result_str.startswith("Error:")
            primary_var_name_for_node = node_to_update.defined_variable

            if primary_var_name_for_node:
                if not script_is_error:
                    last_expr_to_get_aop_value = expr_to_eval.split('\n')[-1].strip()
                    if '=' in last_expr_to_get_aop_value and VARIABLE_REGEX.match(last_expr_to_get_aop_value.lstrip()):
                        last_expr_to_get_aop_value = last_expr_to_get_aop_value.partition('=')[2].strip()
                    if last_expr_to_get_aop_value and not last_expr_to_get_aop_value.startswith("/"):
                        try:
                            rpn_final = getattr(self.calculator, '_rpn_from_expression')(last_expr_to_get_aop_value)
                            val_obj_final = getattr(self.calculator, '_evaluate_rpn')(rpn_final)
                            self.calculator.variables[primary_var_name_for_node] = val_obj_final
                        except Exception as e_final_assign:
                            if primary_var_name_for_node in self.calculator.variables:
                                del self.calculator.variables[primary_var_name_for_node]
                            node_to_update.set_display(f"Error in final assignment to {primary_var_name_for_node}: {e_final_assign}", True)
                            return
                    node_to_update.set_display(script_result_str, script_is_error)
                else:
                    if primary_var_name_for_node in self.calculator.variables:
                        del self.calculator.variables[primary_var_name_for_node]
                    node_to_update.set_display(script_result_str, script_is_error)
            else:
                node_to_update.set_display(script_result_str, script_is_error)

            defined_var = node_to_update.defined_variable
            if defined_var and defined_var in self.dependencies:
                for dependent_node in list(self.dependencies[defined_var]):
                    run_update(dependent_node)
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
