# main.py
import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenuBar, QFileDialog, QToolBar, QButtonGroup,
                               QGraphicsView, QStatusBar, QGraphicsTextItem)
from PySide6.QtGui import QBrush, QPainter, QIntValidator, QKeySequence, QColor, QPainterPath, QAction
from PySide6.QtCore import Qt, QRectF
from aopl_python_impl.aop_calculator import AoP_Calculator
from cosmic_scene import CosmicScene
from gui_items import CalculationNode, TextNoteItem, LineItem, PenStrokeItem
from config import (WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BACKGROUND,
                    COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT, COLOR_TEXT_RESULT,
                    DrawingToolMode)

class CosmicScratchpadWindow(QMainWindow):
    current_drawing_tool: DrawingToolMode
    base_input: QLineEdit

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.current_file_path = None
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create Scene and View FIRST, as other setup methods might need them
        self.scene = CosmicScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.scene.window = self
        self.current_drawing_tool = DrawingToolMode.CALCULATE

        # Create Status Bar early as set_drawing_tool uses it
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(f"QStatusBar {{ color: {COLOR_TEXT_INPUT.name()}; background-color: {COLOR_NODE_BACKGROUND.name()}; }}")
        self.status_bar.showMessage("Ready", 3000)

        # Create Menu Bar
        self.create_menu_bar()
        # Create Toolbar for Drawing Tools
        self.create_drawing_toolbar()
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
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setFrameShape(self.view.Shape.NoFrame)
        # Use a large scene rect for the "infinite" canvas feel
        self.scene.setSceneRect(QRectF(-10000, -10000, 20000, 20000))

    def update_base(self):
        """
        Updates the calculator base when the user changes it.
        """
        self.update_base_from_gui()

    def update_base_from_gui(self):
        """
        Called when Enter is pressed in the GUI base input field.
        """
        self.trigger_base_change_and_full_recalc(self.base_input.text(), command_node=None)

    def trigger_base_change_and_full_recalc(self, new_base_str: str, command_node=None):
        """
        Changes the calculator base and triggers re-evaluation of all nodes.
        """
        original_base_text = self.base_input.text()
        try:
            new_base = int(new_base_str)
            if not (2 <= new_base <= 100):
                msg = f"Error: Base must be between 2 and 100."
                if command_node:
                    command_node.set_display(msg, True)
                self.base_input.setText(original_base_text)
                return
        except ValueError:
            msg = "Error: Invalid base number."
            if command_node:
                command_node.set_display(msg, True)
            self.base_input.setText(original_base_text)
            return

        if self.scene.calculator.base == new_base:
            if command_node:
                command_node.set_display(f"Base is already {new_base}.", False)
            return

        self.scene.calculator.base = new_base
        self.base_input.setText(str(new_base))

        if command_node:
            command_node.set_display(f"Base set to {new_base}. Re-evaluating all nodes...", False)

        nodes_to_update = [item for item in self.scene.items() if isinstance(item, CalculationNode)]
        for node in nodes_to_update:
            if node != command_node:
                self.scene.update_and_propagate(node)

    def update_base_and_reevaluate(self):
        """
        Updates the calculator base and re-evaluates all nodes.
        """
        self.trigger_base_change_and_full_recalc(self.base_input.text(), command_node=None)

    def create_drawing_toolbar(self):
        toolbar = QToolBar("Drawing Tools")
        toolbar.setStyleSheet(f"""
            QToolBar {{ background-color: {COLOR_NODE_BACKGROUND.name()}; border: none; padding: 2px; spacing: 3px; }}
            QToolButton {{ color: {COLOR_TEXT_INPUT.name()}; padding: 4px; border-radius: 3px; margin: 1px; border: 1px solid transparent;}}
            QToolButton:checked {{ background-color: {COLOR_TEXT_RESULT.name()}; color: {COLOR_BACKGROUND.name()}; }}
            QToolButton:hover {{ background-color: {QColor(COLOR_NODE_BACKGROUND).lighter(130).name()}; }}
        """)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self.tool_button_group = QButtonGroup(self)
        self.tool_button_group.setExclusive(True)

        actions_data = [
            ("Calc", DrawingToolMode.CALCULATE, True),
            ("Line", DrawingToolMode.LINE, False),
            ("Text", DrawingToolMode.TEXT_NOTE, False),
            ("Pen", DrawingToolMode.PEN, False)
        ]

        for text, mode, is_checked in actions_data:
            action = QAction(text, self)
            action.setCheckable(True)
            action.setChecked(is_checked)
            action.triggered.connect(lambda is_now_checked, m=mode: self.set_drawing_tool(m) if is_now_checked else None)
            toolbar.addAction(action)
            if is_checked: self.set_drawing_tool(mode)

    def set_drawing_tool(self, tool_mode: DrawingToolMode):
        self.current_drawing_tool = tool_mode
        self.scene.current_drawing_tool = tool_mode

        if tool_mode == DrawingToolMode.CALCULATE:
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.view.setCursor(Qt.CursorShape.IBeamCursor)
        elif tool_mode == DrawingToolMode.TEXT_NOTE:
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.view.setCursor(Qt.CursorShape.IBeamCursor)
        elif tool_mode == DrawingToolMode.LINE:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.view.setCursor(Qt.CursorShape.CrossCursor)
        elif tool_mode == DrawingToolMode.PEN:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.view.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_bar.showMessage(f"{tool_mode.name.replace('_', ' ').title()} Tool Selected", 2000)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(f"""
            QMenuBar {{ background-color: {COLOR_NODE_BACKGROUND.name()}; color: {COLOR_TEXT_INPUT.name()}; }}
            QMenuBar::item:selected {{ background-color: {QColor(COLOR_BACKGROUND).lighter(120).name()}; }}
            QMenu {{ background-color: {COLOR_NODE_BACKGROUND.name()}; color: {COLOR_TEXT_INPUT.name()}; border: 1px solid {COLOR_BACKGROUND.name()};}}
            QMenu::item:selected {{ background-color: {QColor(COLOR_TEXT_RESULT).lighter(120).name()}; color: {COLOR_BACKGROUND.name()}; }}
        """)

        file_menu = menu_bar.addMenu("&File")
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_file)
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("&Edit")
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.edit_undo)
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.edit_redo)
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.edit_cut)
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.edit_copy)
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.edit_paste)
        delete_action = QAction("&Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.edit_delete_selected)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(delete_action)

    def new_file(self):
        # Clear the scene and reset state
        self.scene.clear()
        self.scene.calculator = AoP_Calculator(base=10)
        self.scene.node_definitions = {}
        self.scene.dependencies = {}
        self.base_input.setText("10")
        self.current_file_path = None
        self.setWindowTitle(WINDOW_TITLE)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Cosmic Scratchpad File", "", "Cosmic Files (*.cosmic);;All Files (*)")
        if path:
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                self.new_file()
                self.scene.calculator.base = data.get("base", 10)
                self.base_input.setText(str(self.scene.calculator.base))

                # Load calculation nodes
                for node_data in data.get("nodes", []):
                    node = CalculationNode(self.scene, self.scene.calculator)
                    expr = node_data.get("expression", node_data.get("text", ""))
                    node.expression_str = expr
                    node.setPlainText(expr)
                    node.setPos(node_data.get("pos_x", 0), node_data.get("pos_y", 0))
                    self.scene.addItem(node)

                # Load drawing items
                for item_data in data.get("drawing_items", []):
                    item_type = item_data.get("type")
                    if item_type == "line":
                        line = LineItem(item_data.get("x1",0), item_data.get("y1",0),
                                        item_data.get("x2",0), item_data.get("y2",0))
                        self.scene.addItem(line)
                    elif item_type == "text_note":
                        note = TextNoteItem(item_data.get("text", "Note"))
                        note.setPos(item_data.get("pos_x",0), item_data.get("pos_y",0))
                        self.scene.addItem(note)
                    elif item_type == "pen_stroke":
                        stroke = PenStrokeItem()
                        path = QPainterPath()
                        points_data = item_data.get("points", [])
                        if points_data:
                            first_pt = points_data[0]
                            if first_pt.get("type") == QPainterPath.ElementType.MoveToElement.name:
                                path.moveTo(float(first_pt.get("x", 0)), float(first_pt.get("y", 0)))
                            for pt_data in points_data[1:]:
                                if pt_data.get("type") == QPainterPath.ElementType.LineToElement.name:
                                    path.lineTo(float(pt_data.get("x", 0)), float(pt_data.get("y", 0)))
                        stroke.setPath(path)
                        self.scene.addItem(stroke)

                self.current_file_path = path
                self.setWindowTitle(f"{WINDOW_TITLE} - {path}")

                # After all items are loaded, do a full propagation for calculation nodes
                all_calc_nodes = [item for item in self.scene.items() if isinstance(item, CalculationNode)]
                for node in all_calc_nodes:
                    self.scene.update_and_propagate(node)

            except Exception as e:
                print(f"Error opening file: {e}")

    def save_file(self):
        if self.current_file_path:
            self.perform_save(self.current_file_path)
        else:
            self.save_as_file()

    def save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Cosmic Scratchpad File", "", "Cosmic Files (*.cosmic);;All Files (*)")
        if path:
            self.perform_save(path)
            self.current_file_path = path
            self.setWindowTitle(f"{WINDOW_TITLE} - {path}")

    def get_focused_text_item(self) -> 'QGraphicsTextItem | None':
        focused_item = self.scene.focusItem()
        if isinstance(focused_item, (CalculationNode, TextNoteItem)):
            return focused_item
        return None

    def edit_undo(self):
        item = self.get_focused_text_item()
        if item: item.document().undo()

    def edit_redo(self):
        item = self.get_focused_text_item()
        if item: item.document().redo()

    def edit_cut(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable:
            cursor = item.textCursor()
            if cursor.hasSelection():
                QApplication.clipboard().setText(cursor.selectedText())
                cursor.removeSelectedText()
                item.setTextCursor(cursor)
                if isinstance(item, CalculationNode): item.update_node()

    def edit_copy(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByMouse:
            cursor = item.textCursor()
            if cursor.hasSelection():
                QApplication.clipboard().setText(cursor.selectedText())

    def edit_paste(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable:
            text_to_paste = QApplication.clipboard().text()
            if text_to_paste:
                cursor = item.textCursor()
                cursor.insertText(text_to_paste)
                item.setTextCursor(cursor)
                if isinstance(item, CalculationNode): item.update_node()

    def edit_delete_selected(self):
        # If text is selected in a focused item, delete that text
        focused_text_item = self.get_focused_text_item()
        if focused_text_item and focused_text_item.textCursor().hasSelection():
            focused_text_item.textCursor().removeSelectedText()
            if isinstance(focused_text_item, CalculationNode): focused_text_item.update_node()
            return

        # Otherwise, delete selected graphics items
        items_to_delete = list(self.scene.selectedItems())
        for item_to_del in items_to_delete:
            if isinstance(item_to_del, CalculationNode):
                self.scene.update_node_dependencies(item_to_del)
            if item_to_del.scene() == self.scene:
                self.scene.removeItem(item_to_del)

    def perform_save(self, path):
        data = {
            "version": "0.2",
            "base": self.scene.calculator.base,
            "nodes": [],
            "drawing_items": []
        }
        for item in self.scene.items():
            if isinstance(item, CalculationNode):
                data["nodes"].append({
                    "type": "calculation",
                    "expression": item.expression_str,
                    "pos_x": item.pos().x(),
                    "pos_y": item.pos().y()
                })
            elif isinstance(item, LineItem):
                line = item.line()
                data["drawing_items"].append({
                    "type": "line",
                    "x1": line.x1(), "y1": line.y1(),
                    "x2": line.x2(), "y2": line.y2(),
                })
            elif isinstance(item, TextNoteItem):
                data["drawing_items"].append({
                    "type": "text_note",
                    "text": item.toPlainText(),
                    "pos_x": item.pos().x(),
                    "pos_y": item.pos().y(),
                })
            elif isinstance(item, PenStrokeItem):
                path_points = []
                element_type_names = {
                    QPainterPath.ElementType.MoveToElement: QPainterPath.ElementType.MoveToElement.name,
                    QPainterPath.ElementType.LineToElement: QPainterPath.ElementType.LineToElement.name
                }
                for i in range(item.path().elementCount()):
                    el = item.path().elementAt(i)
                    try:
                        x_val = getattr(el, 'x', lambda: 0)() if callable(getattr(el, 'x', None)) else 0
                        y_val = getattr(el, 'y', lambda: 0)() if callable(getattr(el, 'y', None)) else 0
                        el_type = getattr(el, 'type', lambda: None)()
                        type_val = element_type_names.get(el_type, 'Unknown') if el_type is not None else 'Unknown'
                        path_points.append({"x": x_val, "y": y_val, "type": type_val})
                    except Exception:
                        path_points.append({"x": 0, "y": 0, "type": "Unknown"})
                data["drawing_items"].append({
                    "type": "pen_stroke",
                    "points": path_points,
                })
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving file: {e}")

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
