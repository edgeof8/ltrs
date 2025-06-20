# cosmic_scratchpad.py (Final Refactored Version)
import sys
import re
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                               QGraphicsTextItem, QMainWindow, QWidget,
                               QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QGraphicsItemGroup, QMenu)
from PySide6.QtGui import QColor, QBrush, QFont, QTextCursor, QIntValidator
from PySide6.QtCore import Qt, QRectF

# Backend Import
from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.definitions import OutputFormatMode

# --- Configuration ---
WINDOW_TITLE = "Cosmic Scratchpad v0.2"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FONT_FAMILY = "Courier New"
FONT_SIZE = 14
COLOR_BACKGROUND = QColor("#1e1e2e")
COLOR_TEXT_INPUT = QColor("#cdd6f4")
COLOR_NODE_BACKGROUND = QColor("#313244") # A slightly lighter shade for the node background
COLOR_TEXT_RESULT = QColor("#89b4fa") # A nice "nebula blue"
COLOR_NUMBER_DIM = QColor("#585b70") # New color for the dimmed part of the number
COLOR_TEXT_SUFFIX = QColor("#f9e2af") # A warm "gold" for the suffix
COLOR_TEXT_ERROR = QColor("#f38ba8")
VARIABLE_REGEX = re.compile(r"\$([a-zA-Z_]\w*)")

# --- Suffix Logic ---
from aopl_python_impl.definitions import EXPONENT_TO_LETTER_MAP
DIGIT_COUNT_TO_AOP_LETTER = {i: EXPONENT_TO_LETTER_MAP.get(i, '') for i in range(1, 52)}

def get_aop_suffix(num_str: str) -> str:
    length = len(num_str.lstrip('-'))
    return DIGIT_COUNT_TO_AOP_LETTER.get(length, '')

def format_annotated_number(number_str: str) -> str:
    """
    Generates HTML to style a large number, highlighting the last digit.
    """
    dim_part = number_str[:-1]
    highlight_part = number_str[-1]
    return (f"<span style='color: {COLOR_NUMBER_DIM.name()};'>{dim_part}</span>"
            f"<span style='color: {COLOR_TEXT_SUFFIX.name()};'>{highlight_part}</span>")

class CalculationNode(QGraphicsTextItem):
    """The main, editable calculation node."""
    def __init__(self, scene, calculator):
        super().__init__()
        self.scene = scene
        self.calculator = calculator
        self.expression_str = ""
        self.defined_variable = None
        self.dependencies = set()

        self.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.setDefaultTextColor(COLOR_TEXT_INPUT)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        from PySide6.QtWidgets import QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPlainText("")
        self.document().setDocumentMargin(8)
        self.update_node()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() != Qt.KeyboardModifier.ShiftModifier:
                self.clearFocus()
                return
        super().keyPressEvent(event)
        self.update_node()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        if not self.toPlainText().strip():
            self.scene.removeItem(self)  # Simplified destruction
            return
        self.update_node()

    def paint(self, painter, option, widget=None):
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QWidget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        super().paint(painter, option, widget if widget else QWidget())

    def contextMenuEvent(self, event):
        menu = QMenu()
        action_cut = menu.addAction("Cut")
        action_copy = menu.addAction("Copy")
        action_paste = menu.addAction("Paste")

        def cut():
            cursor = self.textCursor()
            if cursor.hasSelection():
                QApplication.clipboard().setText(cursor.selectedText())
                cursor.removeSelectedText()
                self.setTextCursor(cursor)

        def copy():
            cursor = self.textCursor()
            if cursor.hasSelection():
                QApplication.clipboard().setText(cursor.selectedText())

        def paste():
            text = QApplication.clipboard().text()
            if text:
                cursor = self.textCursor()
                cursor.insertText(text)
                self.setTextCursor(cursor)

        action_cut.triggered.connect(cut)
        action_copy.triggered.connect(copy)
        action_paste.triggered.connect(paste)
        menu.exec(event.screenPos())

    def update_node(self):
        self.scene.update_and_propagate(self)

    def set_display(self, result_str, is_error, number_to_format, suffix_text):
        # Main logic for displaying text and managing the suffix node.
        safe_expression = self.expression_str.replace('<', '<').replace('>', '>')

        if result_str:
            color = COLOR_TEXT_ERROR if is_error else COLOR_TEXT_RESULT
            final_result_html = result_str
            # Replace the number with the styled version
            if number_to_format and not is_error:
                styled_number_html = format_annotated_number(number_to_format)
                final_result_html = result_str.replace(number_to_format, styled_number_html)
            else:
                final_result_html = result_str

            html_content = (f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression}</span> "
                           f"<span style='color: {color.name()};'>→ {final_result_html}</span>")
        else:
            html_content = f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression}</span>"

        cursor = self.textCursor()
        cursor_pos = cursor.position()
        self.setHtml(html_content)
        cursor.setPosition(cursor_pos)
        self.setTextCursor(cursor)
        self.document().adjustSize()


class CosmicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calculator = AoP_Calculator(base=10)
        self.node_definitions = {}
        self.dependencies = {}

    def mousePressEvent(self, event):
        for item in list(self.items()):
            if isinstance(item, CalculationNode) and not item.hasFocus() and not item.toPlainText().strip():
                self.removeItem(item)
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if item:
            super().mousePressEvent(event)
            return
        pos = event.scenePos()
        new_node = CalculationNode(self, self.calculator)
        self.addItem(new_node)
        new_node.setPos(pos)
        new_node.setFocus()
        super().mousePressEvent(event)

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
                node_to_update.set_display("", False, "", "")
                return
            if any(clean_expr.endswith(op) for op in ['+', '-', '*', '/', '^', '**']):
                node_to_update.set_display("", False, "", "")
                return

            self.update_node_dependencies(node_to_update)

            expr_to_eval = clean_expr
            is_assignment = '=' in expr_to_eval
            if is_assignment:
                var_name, _, expr_to_eval_rhs = expr_to_eval.partition('=')
                var_name = var_name.strip()
                if not VARIABLE_REGEX.match(var_name):
                    msg = "Invalid variable name. Variables must start with a '$'."
                    node_to_update.set_display(msg, True, "")
                    return
                expr_to_eval = expr_to_eval_rhs.strip()

            result_str = self.evaluate_script(expr_to_eval)
            is_error = result_str.startswith("Error:")

            # --- Suffix logic now finds the number to format ---
            number_to_format = ""
            if not is_error:
                # Find large numbers in the result and get their suffix
                large_num_match = re.search(r'\d{4,}', result_str)
                if large_num_match:
                    number_to_format = large_num_match.group(0)

            if is_assignment and not is_error:
                rpn = getattr(self.calculator, '_rpn_from_expression')(expr_to_eval)
                val_obj = getattr(self.calculator, '_evaluate_rpn')(rpn)
                self.calculator.variables[var_name] = val_obj
                node_to_update.set_display(result_str, False, number_to_format, "")
            elif is_assignment and is_error:
                if var_name in self.calculator.variables: del self.calculator.variables[var_name]
                node_to_update.set_display(result_str, True, "", "")
            else:
                node_to_update.set_display(result_str, is_error, number_to_format, "")

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
        statements = [s.strip() for s in script_string.split(';') if s.strip()]
        if not statements: return ""
        final_result = ""
        for statement in statements:
            final_result = self.calculator.evaluate_expression(
                expression=statement, mode=OutputFormatMode.AUTO, precision=10)
        return final_result

class CosmicScratchpadWindow(QMainWindow):
    # ... (This class remains the same) ...
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.scene = CosmicScene(self)
        self.view = QGraphicsView(self.scene, self)
        layout.addWidget(self.view)
        control_deck = QWidget()
        control_deck.setStyleSheet(f"background-color: {COLOR_NODE_BACKGROUND.name()}; color: {COLOR_TEXT_INPUT.name()};")
        control_deck_layout = QHBoxLayout(control_deck)
        control_deck_layout.setContentsMargins(10, 5, 10, 5)
        base_label = QLabel("Base:")
        self.base_input = QLineEdit(str(self.scene.calculator.base))
        self.base_input.setValidator(QIntValidator(2, 100))
        self.base_input.setFixedWidth(50)
        self.base_input.setStyleSheet(f"background-color: {COLOR_BACKGROUND.name()}; border: 1px solid {COLOR_TEXT_RESULT.name()};")
        self.base_input.returnPressed.connect(self.update_base)
        control_deck_layout.addWidget(base_label)
        control_deck_layout.addWidget(self.base_input)
        control_deck_layout.addStretch()
        layout.addWidget(control_deck)
        self.view.setBackgroundBrush(QBrush(COLOR_BACKGROUND))
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        self.view.setFrameShape(self.view.Shape.NoFrame)
        self.scene.setSceneRect(QRectF(0, 0, 5000, 5000))

    def update_base(self):
        new_base = int(self.base_input.text())
        self.scene.calculator.base = new_base
        for item in self.scene.items():
            if isinstance(item, CalculationNode):
                item.update_node()

# Monkey-patching for compatibility
def rpn_from_expression(self, expression):
    from aopl_python_impl.aop_parser import tokenize_expression, infix_to_rpn
    tokens = tokenize_expression(expression, self.token_regex)
    return infix_to_rpn(tokens, self.operators_map)

def evaluate_rpn_only(self, rpn):
    from aopl_python_impl.aop_parser import evaluate_rpn
    from aopl_python_impl.aop_operations import simplify_value
    from aopl_python_impl.aop_term_handler import get_term_value
    result = evaluate_rpn(rpn, self.variables, get_term_value, self.base)
    return simplify_value(result, self.base)

# Use setattr to avoid direct attribute assignment issues
setattr(AoP_Calculator, '_rpn_from_expression', rpn_from_expression)
setattr(AoP_Calculator, '_evaluate_rpn', evaluate_rpn_only)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CosmicScratchpadWindow()
    window.show()
    sys.exit(app.exec())
