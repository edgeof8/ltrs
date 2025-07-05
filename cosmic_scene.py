import sys
from pathlib import Path

# --- Add project root to sys.path ---
# This allows this module to find the aopl_python_impl module when imported by main.py
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
# ------------------------------------

# cosmic_scene.py
import typing
import re
from PySide6.QtWidgets import QGraphicsScene, QToolBar, QApplication, QMenu, QInputDialog, QGraphicsLineItem, QGraphicsItem
from PySide6.QtGui import QPainterPath, QTextOption, QAction, QPen
from PySide6.QtCore import Qt
from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.constants import LETTER_TO_EXPONENT_MAP
from aopl_python_impl import aop_ai_explainer
from aopl_python_impl.aop_formatter import format_as_decimal_string
from gui_items.calculation_node import CalculationNode
from gui_items.line_item import LineItem
from gui_items.text_note_item import TextNoteItem
from gui_items.pen_stroke_item import PenStrokeItem
from gui_items.plot_node import PlotNode
from gui_items.base_item import ResizableTextItem
from config import DrawingToolMode, VARIABLE_REGEX

if typing.TYPE_CHECKING:
    from main import CosmicScratchpadWindow

class CosmicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calculator = AoP_Calculator(base=10) # Removed load_default_vars
        self.node_definitions = {}
        self.dependencies = {}
        self.window: 'CosmicScratchpadWindow | None' = None
        self.drawing_toolbar: 'QToolBar | None' = None
        self.current_drawing_tool: DrawingToolMode = DrawingToolMode.CALCULATE
        self.current_line_item = None
        self.current_pen_stroke = None
        self.last_pen_point = None
        self.last_evaluated_calc_node: CalculationNode | None = None
        self.current_ai_model: str = "deepseek/deepseek-chat-v3-0324:free"
        self.guide_lines = []
        self.current_moving_item = None
        self.snap_guides = []

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
            "/explain": self._handle_explain,
            "/plot": self._handle_plot
        }

    # --- COMMAND HANDLERS START ---

    def _handle_vars(self, context, node, calculator=None):
        var_list_str = "Variables:\n"
        if calculator and calculator.variables:
            for var_name, aop_value in sorted(calculator.variables.items()):
                val_str_direct = format_as_decimal_string(aop_value) # Changed to format_as_decimal_string
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
        base = calculator.base if calculator else self.calculator.base
        command_output = f"Current base: {base}"
        node.set_display(command_output, False)

    def _handle_setbase(self, context, node, calculator=None):
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

    def _handle_constants(self, context, node, calculator=None):
        known_constants = ["#pi", "#e", "#phi", "#tau", "#sqrt2", "#j", "#sqrt3", "#ln2"]
        command_output = "Predefined Constants:\n"
        calc_to_use = calculator if calculator else self.calculator
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
        if calculator:
            calculator.variables.clear()
        else:
            self.calculator.variables.clear()
        node.set_display("All user variables cleared.", False)
        # Re-evaluate nodes to show errors for undefined variables
        for item in self.items():
            if isinstance(item, CalculationNode) and item != node:
                item.update_node_and_propagate() # type: ignore

    def _handle_delvar(self, context, node, calculator=None):
        args = context['first_line_args']
        if args:
            var_name = args[0]
            if not var_name.startswith("$"):
                var_name = f"${var_name}"
            calc = calculator if calculator else self.calculator
            if var_name in calc.variables:
                del calc.variables[var_name]
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

    def _handle_reset(self, context, node, calculator=None):
        self.calculator = AoP_Calculator(base=10) # Removed load_default_vars
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
                item.update_node_and_propagate() # type: ignore


    def _handle_explain(self, context, node, calculator=None):
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
            calc_to_use = calculator if calculator else self.calculator
            temp_calc = AoP_Calculator(base=calc_to_use.base) # Removed load_default_vars
            temp_calc.variables = calc_to_use.variables.copy()
            ai_target_result_str, _ = temp_calc.evaluate_expression(ai_target_expr_str, "num") # Adjusted call
            if ai_target_result_str.startswith("Error:"):
                command_output = f"Error evaluating for explanation: {ai_target_result_str}"
                is_error_output = True
            else:
                _, ast_for_explainer = temp_calc.evaluate_expression(ai_target_expr_str, "num")
                if ast_for_explainer is None:
                    command_output = "Error: Could not parse expression for AI explanation."
                    is_error_output = True
                else:
                    # The get_ai_explanation_and_session function returns a tuple (AIConversation, str)
                    # We only need the string explanation here.
                    _, explanation = aop_ai_explainer.get_ai_explanation_and_session(ai_target_expr_str, ai_target_result_str, calc_to_use.base, ast_for_explainer)
                    if explanation is None:
                        command_output = "Error: AI explanation service failed."
                        is_error_output = True
                    else:
                        command_output = explanation
                        is_error_output = explanation.startswith("Error:")

        node.set_display(command_output, is_error_output, is_command_output=True)

    # --- COMMAND HANDLERS END ---

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
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton
            class PlotConfigDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Plot Configuration")
                    layout = QVBoxLayout(self)

                    # Expression
                    expr_layout = QHBoxLayout()
                    expr_label = QLabel("Expression:")
                    self.expr_input = QLineEdit()
                    expr_layout.addWidget(expr_label)
                    expr_layout.addWidget(self.expr_input)
                    layout.addLayout(expr_layout)

                    # Variable
                    var_layout = QHBoxLayout()
                    var_label = QLabel("Variable:")
                    self.var_input = QLineEdit()
                    var_layout.addWidget(var_label)
                    var_layout.addWidget(self.var_input)
                    layout.addLayout(var_layout)

                    # Start Value
                    start_layout = QHBoxLayout()
                    start_label = QLabel("Start Value:")
                    self.start_input = QLineEdit("1")
                    start_layout.addWidget(start_label)
                    start_layout.addWidget(self.start_input)
                    layout.addLayout(start_layout)

                    # End Value
                    end_layout = QHBoxLayout()
                    end_label = QLabel("End Value:")
                    self.end_input = QLineEdit("100")
                    end_layout.addWidget(end_label)
                    end_layout.addWidget(self.end_input)
                    layout.addLayout(end_layout)

                    # Steps
                    steps_layout = QHBoxLayout()
                    steps_label = QLabel("Steps:")
                    self.steps_input = QLineEdit("200")
                    steps_layout.addWidget(steps_label)
                    steps_layout.addWidget(self.steps_input)
                    layout.addLayout(steps_layout)

                    # Logarithmic options
                    self.log_x_check = QCheckBox("Logarithmic X-axis")
                    self.log_y_check = QCheckBox("Logarithmic Y-axis")
                    layout.addWidget(self.log_x_check)
                    layout.addWidget(self.log_y_check)

                    # Buttons
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

        calc_to_use = calculator if calculator else self.calculator
        plot_node = PlotNode(self, calc_to_use, expression, variable[1:], start_val, end_val, steps, log_x, log_y)
        self.addItem(plot_node)
        plot_node.setPos(node.pos().x() + 50, node.pos().y() + 50)
        node.set_display(f"Plot created for {expression}", False)
        self.update_node_dependencies(plot_node)

    def show_context_menu(self, event):
        """
        Builds and displays a context menu on right-click.
        """
        item_at_click = self.itemAt(event.scenePos(), self.views()[0].transform())
        menu = QMenu()

        # Add standard actions (Cut, Copy, Paste) if applicable
        if isinstance(item_at_click, (CalculationNode, TextNoteItem)):
            if hasattr(item_at_click, 'cut'):
                cut_action = QAction("Cut", menu)
                cut_action.triggered.connect(item_at_click.cut) # type: ignore
                menu.addAction(cut_action)

            if hasattr(item_at_click, 'copy'):
                copy_action = QAction("Copy", menu)
                copy_action.triggered.connect(item_at_click.copy) # type: ignore
                menu.addAction(copy_action)

            if hasattr(item_at_click, 'paste'):
                paste_action = QAction("Paste", menu)
                paste_action.triggered.connect(item_at_click.paste) # type: ignore
                menu.addAction(paste_action)
            menu.addSeparator()

        # Add command submenu
        command_menu = menu.addMenu("Execute Command...")
        for command in sorted(self.command_handlers.keys()):
            action = QAction(command, command_menu)
            action.triggered.connect(lambda checked, cmd=command, pos=event.scenePos(): self.handle_menu_command(cmd, pos))
            command_menu.addAction(action)

        # Show the menu at the click position
        menu.exec(event.screenPos())

    def handle_menu_command(self, command_str, position):
        """
        Handles the execution of a command selected from the context menu.
        """
        # Commands that require user input
        input_commands = ["/setbase", "/delvar", "/undef", "/explain"]
        command_lower = command_str.lower()

        full_command = command_str
        if any(cmd in command_lower for cmd in input_commands):
            # Prompt for input
            prompt_text = "Enter argument(s) for " + command_str + ":"
            if command_lower == "/setbase":
                prompt_text = "Enter new base:"
            elif command_lower in ["/delvar", "/undef"]:
                prompt_text = "Enter variable name to delete:"
            elif command_lower == "/explain":
                prompt_text = "Enter expression or 'last' for previous calculation:"

            text, ok = QInputDialog.getText(None, "Input Required", prompt_text)
            if ok and text:
                full_command = f"{command_str} {text}"

        # Create a new CalculationNode at the click position
        new_node = CalculationNode(self, self.calculator)
        self.addItem(new_node)
        new_node.setPos(position)
        new_node.setPlainText(full_command)
        self.update_and_propagate(new_node)


    def mousePressEvent(self, event):
        # Janitorial sweep for empty CalculationNodes (only in calc mode)
        if self.current_drawing_tool == DrawingToolMode.CALCULATE:
            for item in list(self.items()):
                if isinstance(item, CalculationNode) and not item.hasFocus() and not item.toPlainText().strip(): # type: ignore
                    self.removeItem(item)

        item_at_click = self.itemAt(event.scenePos(), self.views()[0].transform())

        if event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)
            event.accept()
            return

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

        # Clear snap guides on mouse release
        self._clear_snap_guides()
        self.current_moving_item = None

        super().mouseReleaseEvent(event)

    def _clear_guide_lines(self):
        for line in self.guide_lines:
            if line in self.items():
                self.removeItem(line)
        self.guide_lines = []

    def _clear_snap_guides(self):
        for line in self.snap_guides:
            if line in self.items():
                self.removeItem(line)
        self.snap_guides = []

    def _show_snap_guide(self, axis: str, position: float):
        scene_rect = self.sceneRect()
        if axis == "x":
            line = QGraphicsLineItem(position, scene_rect.top(), position, scene_rect.bottom())
            line.setPen(QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine))
        else:  # axis == "y"
            line = QGraphicsLineItem(scene_rect.left(), position, scene_rect.right(), position)
            line.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine))
        self.addItem(line)
        self.snap_guides.append(line)

    def _update_guide_lines(self, item):
        if not isinstance(item, ResizableTextItem):
            return
        self._clear_guide_lines()
        tolerance = 5.0
        item_rect = item.sceneBoundingRect()
        item_top = item_rect.top()
        item_center_y = item_rect.center().y()
        item_bottom = item_rect.bottom()
        item_left = item_rect.left()
        item_center_x = item_rect.center().x()
        item_right = item_rect.right()

        scene_rect = self.sceneRect()
        guide_pen_h = QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine)
        guide_pen_v = QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine)

        for other in self.items():
            if other == item or not isinstance(other, ResizableTextItem):
                continue
            other_rect = other.sceneBoundingRect()
            other_top = other_rect.top()
            other_center_y = other_rect.center().y()
            other_bottom = other_rect.bottom()
            other_left = other_rect.left()
            other_center_x = other_rect.center().x()
            other_right = other_rect.right()

            # Horizontal guides
            if abs(item_top - other_top) < tolerance:
                line = QGraphicsLineItem(scene_rect.left(), other_top, scene_rect.right(), other_top)
                line.setPen(guide_pen_h)
                self.addItem(line)
                self.guide_lines.append(line)
            elif abs(item_center_y - other_center_y) < tolerance:
                line = QGraphicsLineItem(scene_rect.left(), other_center_y, scene_rect.right(), other_center_y)
                line.setPen(guide_pen_h)
                self.addItem(line)
                self.guide_lines.append(line)
            elif abs(item_bottom - other_bottom) < tolerance:
                line = QGraphicsLineItem(scene_rect.left(), other_bottom, scene_rect.right(), other_bottom)
                line.setPen(guide_pen_h)
                self.addItem(line)
                self.guide_lines.append(line)

            # Vertical guides
            if abs(item_left - other_left) < tolerance:
                line = QGraphicsLineItem(other_left, scene_rect.top(), other_left, scene_rect.bottom())
                line.setPen(guide_pen_v)
                self.addItem(line)
                self.guide_lines.append(line)
            elif abs(item_center_x - other_center_x) < tolerance:
                line = QGraphicsLineItem(other_center_x, scene_rect.top(), other_center_x, scene_rect.bottom())
                line.setPen(guide_pen_v)
                self.addItem(line)
                self.guide_lines.append(line)
            elif abs(item_right - other_right) < tolerance:
                line = QGraphicsLineItem(other_right, scene_rect.top(), other_right, scene_rect.bottom())
                line.setPen(guide_pen_v)
                self.addItem(line)
                self.guide_lines.append(line)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                if isinstance(item, CalculationNode):
                    # Find any nodes that depend on a variable this node defines
                    if item.defined_variable and item.defined_variable in self.dependencies: # type: ignore
                        dependents = list(self.dependencies[item.defined_variable]) # type: ignore
                        for dep_node in dependents:
                            dep_node.update_node_and_propagate() # Re-evaluate to show error
                    # Remove the variable from the calculator and our tracking
                    if item.defined_variable in self.calculator.variables: # type: ignore
                        del self.calculator.variables[item.defined_variable] # type: ignore
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
                handler(context, start_node, self.calculator)
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
                        if isinstance(dependent_node, PlotNode):
                            dependent_node.redraw_plot()
                        else:
                            self.update_and_propagate(dependent_node, propagate=True)

    def update_node_dependencies(self, node):
        if node in self.node_definitions:
            old_var_name = self.node_definitions.pop(node)
            if old_var_name in self.calculator.variables: del self.calculator.variables[old_var_name]

        if node.dependencies:
            for var in node.dependencies:
                if var in self.dependencies: self.dependencies[var].discard(node)

        if isinstance(node, CalculationNode):
            match = re.match(r"^\s*(\$[a-zA-Z_]\w*)\s*=", node.expression_str)
            if match:
                node.defined_variable = match.group(1)
                self.node_definitions[node] = node.defined_variable
            else:
                node.defined_variable = None
            node.dependencies = set(VARIABLE_REGEX.findall(node.expression_str))
        elif isinstance(node, PlotNode):
            node.defined_variable = None
            node.dependencies = set(VARIABLE_REGEX.findall(node.expression) + VARIABLE_REGEX.findall(node.start_val) + VARIABLE_REGEX.findall(node.end_val))

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
        temp_calculator = AoP_Calculator(base=self.calculator.base) # Removed load_default_vars
        temp_calculator.variables = self.calculator.variables.copy()

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
        self.calculator.variables = temp_calculator.variables
        return final_result_str

    def generate_python_script(self) -> str:
        """
        Generates a linear, executable Python script from the dependency graph of CalculationNodes.
        Uses topological sort to ensure correct execution order.
        """
        from collections import deque

        # Header for the script
        script_lines = [
            "# Generated by Cosmic Scratchpad",
            "# This script replicates the calculations from the visual dependency graph.",
            "from aopl_python_impl.aop_calculator import AoP_Calculator",
            "",
            f"calc = AoP_Calculator(base={self.calculator.base})",
            ""
        ]

        # Collect all calculation nodes
        calc_nodes = [item for item in self.items() if isinstance(item, CalculationNode)]
        if not calc_nodes:
            script_lines.append("# No calculation nodes to export.")
            return "\n".join(script_lines)

        # Build the graph for topological sort
        in_degree = {node: 0 for node in calc_nodes}
        graph = {node: set() for node in calc_nodes}

        # Create a reverse mapping from variable name to the node that defines it
        var_to_def_node = {v: k for k, v in self.node_definitions.items()}

        # Populate the graph based on dependencies (correct direction: source -> dependent)
        for node in calc_nodes:
            for var in node.dependencies: # type: ignore
                source_node = var_to_def_node.get(f"${var}")
                if source_node and source_node in calc_nodes and source_node != node:
                    graph[source_node].add(node)
                    in_degree[node] = in_degree.get(node, 0) + 1

        # Perform topological sort using Kahn's algorithm
        queue = deque([node for node, deg in in_degree.items() if deg == 0])
        sorted_nodes = []

        while queue:
            node = queue.popleft()
            sorted_nodes.append(node)
            for dep_node in graph[node]:
                in_degree[dep_node] -= 1
                if in_degree[dep_node] == 0:
                    queue.append(dep_node)

        # Check for cycles (if not all nodes are in sorted_nodes, there is a cycle)
        if len(sorted_nodes) != len(calc_nodes):
            script_lines.append("# Warning: Dependency cycle detected. Execution order may not be complete.")
            # Add remaining nodes that weren't processed due to cycles
            remaining = [node for node in calc_nodes if node not in sorted_nodes]
            sorted_nodes.extend(remaining)

        # Identify sink nodes (nodes that no other node depends on)
        sink_nodes = set(calc_nodes)
        for node in calc_nodes:
            for dep_node in graph[node]:
                if dep_node in sink_nodes:
                    sink_nodes.remove(dep_node)

        # Generate script lines for each node in topological order
        for i, node in enumerate(sorted_nodes):
            pos_x, pos_y = node.pos().x(), node.pos().y()
            script_lines.append(f"# Node {i+1} at position ({pos_x:.0f}, {pos_y:.0f})")
            expr = node.expression_str.replace('"', '\\"').replace("'", "\\'")
            script_lines.append(f'result_{i+1} = calc.evaluate_expression(expression="""{expr}""")[0]')
            if node in sink_nodes and i == len(sorted_nodes) - 1:
                script_lines.append(f'print("Final Result: ", result_{i+1})')
            script_lines.append("")

        return "\n".join(script_lines)
