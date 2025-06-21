# main.py
import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenuBar, QFileDialog, QToolBar, QButtonGroup,
                               QGraphicsView, QStatusBar, QGraphicsTextItem)
from PySide6.QtGui import QBrush, QPainter, QIntValidator, QKeySequence, QColor, QPainterPath, QAction
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from aopl_python_impl.aop_calculator import AoP_Calculator
from cosmic_scene import CosmicScene
from gui_items import CalculationNode, TextNoteItem, LineItem, PenStrokeItem, ResizableTextItem
from config import (WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BACKGROUND,
                    COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT, COLOR_TEXT_RESULT,
                    DrawingToolMode)

class CosmicView(QGraphicsView):
    scenePosChanged = Signal(QPointF)
    zoomChanged = Signal(float)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.panning = False

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
            self.scale(zoom_factor, zoom_factor)
            self.zoomChanged.emit(self.transform().m11())
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        is_panning_key = event.button() == Qt.MiddleButton or \
                         (event.button() == Qt.LeftButton and QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)

        if is_panning_key:
            self.panning = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.GrabbingHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # FIX: Use event.position() instead of event.pos() to resolve deprecation warning.
        scene_pos = self.mapToScene(event.position().toPoint())
        self.scenePosChanged.emit(scene_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.unsetCursor()
        super().mouseReleaseEvent(event)


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

        self.scene = CosmicScene(self)
        self.view = CosmicView(self.scene, self)
        self.scene.window = self
        self.current_drawing_tool = DrawingToolMode.CALCULATE

        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(f"QStatusBar {{ color: {COLOR_TEXT_INPUT.name()}; background-color: {COLOR_NODE_BACKGROUND.name()}; }}")
        self.status_bar.showMessage("Ready", 3000)

        self.coord_label = QLabel("X: 0, Y: 0")
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addPermanentWidget(self.coord_label)
        self.status_bar.addPermanentWidget(self.zoom_label)

        self.view.scenePosChanged.connect(self.update_coords)
        self.view.zoomChanged.connect(self.update_zoom)
        self.update_zoom(1.0) # Set initial zoom

        self.create_menu_bar()
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
        self.scene.setSceneRect(QRectF(-10000, -10000, 20000, 20000))

        # --- FIX: Center the view on the origin at startup ---
        self.view.centerOn(0, 0)

    def update_coords(self, pos: QPointF):
        self.coord_label.setText(f"X: {pos.x():.0f}, Y: {pos.y():.0f}")

    def update_zoom(self, zoom_level: float):
        self.zoom_label.setText(f"Zoom: {zoom_level*100:.0f}%")

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
            action.triggered.connect(lambda checked, m=mode: self.set_drawing_tool(m) if checked else None)
            toolbar.addAction(action)

            button = toolbar.widgetForAction(action)
            if button:
                self.tool_button_group.addButton(button)

            if is_checked: self.set_drawing_tool(mode)

    def update_base(self): self.trigger_base_change_and_full_recalc(self.base_input.text())

    def trigger_base_change_and_full_recalc(self, new_base_str: str, command_node=None):
        original_base_text = self.base_input.text()
        try:
            new_base = int(new_base_str)
            if not (2 <= new_base <= 100):
                msg = f"Error: Base must be between 2 and 100."
                if command_node: command_node.set_display(msg, True)
                self.base_input.setText(original_base_text)
                return
        except ValueError:
            msg = "Error: Invalid base number."
            if command_node: command_node.set_display(msg, True)
            self.base_input.setText(original_base_text)
            return
        if self.scene.calculator.base == new_base:
            if command_node: command_node.set_display(f"Base is already {new_base}.", False)
            return
        self.scene.calculator.base = new_base
        self.base_input.setText(str(new_base))
        if command_node: command_node.set_display(f"Base set to {new_base}. Re-evaluating all nodes...", False)
        nodes_to_update = [item for item in self.scene.items() if isinstance(item, CalculationNode)]
        for node in nodes_to_update:
            if node != command_node:
                self.scene.update_and_propagate(node)

    def set_drawing_tool(self, tool_mode: DrawingToolMode):
        self.current_drawing_tool = tool_mode
        self.scene.current_drawing_tool = tool_mode
        if tool_mode in (DrawingToolMode.CALCULATE, DrawingToolMode.TEXT_NOTE):
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.view.setCursor(Qt.CursorShape.IBeamCursor)
        else:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            if tool_mode == DrawingToolMode.LINE: self.view.setCursor(Qt.CursorShape.CrossCursor)
            elif tool_mode == DrawingToolMode.PEN: self.view.setCursor(Qt.CursorShape.PointingHandCursor)
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
        new_action = QAction("&New", self); new_action.setShortcut(QKeySequence.StandardKey.New); new_action.triggered.connect(self.new_file)
        open_action = QAction("&Open...", self); open_action.setShortcut(QKeySequence.StandardKey.Open); open_action.triggered.connect(self.open_file)
        save_action = QAction("&Save", self); save_action.setShortcut(QKeySequence.StandardKey.Save); save_action.triggered.connect(self.save_file)
        save_as_action = QAction("Save &As...", self); save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs); save_as_action.triggered.connect(self.save_as_file)
        exit_action = QAction("E&xit", self); exit_action.setShortcut(QKeySequence.StandardKey.Quit); exit_action.triggered.connect(self.close)
        file_menu.addAction(new_action); file_menu.addAction(open_action); file_menu.addAction(save_action); file_menu.addAction(save_as_action); file_menu.addSeparator(); file_menu.addAction(exit_action)
        edit_menu = menu_bar.addMenu("&Edit")
        undo_action = QAction("&Undo", self); undo_action.setShortcut(QKeySequence.StandardKey.Undo); undo_action.triggered.connect(self.edit_undo)
        redo_action = QAction("&Redo", self); redo_action.setShortcut(QKeySequence.StandardKey.Redo); redo_action.triggered.connect(self.edit_redo)
        cut_action = QAction("Cu&t", self); cut_action.setShortcut(QKeySequence.StandardKey.Cut); cut_action.triggered.connect(self.edit_cut)
        copy_action = QAction("&Copy", self); copy_action.setShortcut(QKeySequence.StandardKey.Copy); copy_action.triggered.connect(self.edit_copy)
        paste_action = QAction("&Paste", self); paste_action.setShortcut(QKeySequence.StandardKey.Paste); paste_action.triggered.connect(self.edit_paste)
        delete_action = QAction("&Delete", self); delete_action.setShortcut(QKeySequence.StandardKey.Delete); delete_action.triggered.connect(self.edit_delete_selected)
        edit_menu.addAction(undo_action); edit_menu.addAction(redo_action); edit_menu.addSeparator(); edit_menu.addAction(cut_action); edit_menu.addAction(copy_action); edit_menu.addAction(paste_action); edit_menu.addSeparator(); edit_menu.addAction(delete_action)

    def new_file(self):
        self.scene.clear()
        self.scene.calculator = AoP_Calculator(base=10, load_default_vars=True)
        self.scene.node_definitions = {}
        self.scene.dependencies = {}
        self.base_input.setText("10")
        self.current_file_path = None
        self.setWindowTitle(WINDOW_TITLE)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Cosmic Scratchpad File", "", "Cosmic Files (*.cosmic);;All Files (*)")
        if not path: return
        try:
            with open(path, 'r') as f: data = json.load(f)
            self.new_file()
            self.scene.calculator.base = data.get("base", 10)
            self.base_input.setText(str(self.scene.calculator.base))
            nodes_to_process = []
            for node_data in data.get("nodes", []):
                node = CalculationNode(self.scene, self.scene.calculator)
                expr = node_data.get("expression", "")
                node.expression_str = expr
                node.setPlainText(expr)
                node.setPos(node_data.get("pos_x", 0), node_data.get("pos_y", 0))
                # Restore size if saved
                if "width" in node_data and "height" in node_data:
                    node.document().setTextWidth(node_data["width"] - 2 * node.document().documentMargin())
                    node._user_has_resized = True
                    node._update_wrap_mode_based_on_state()
                self.scene.addItem(node)
                nodes_to_process.append(node)

            for item_data in data.get("drawing_items", []):
                item_type = item_data.get("type")
                if item_type == "line": self.scene.addItem(LineItem(item_data.get("x1",0), item_data.get("y1",0), item_data.get("x2",0), item_data.get("y2",0)))
                elif item_type == "text_note":
                    note = TextNoteItem(item_data.get("text", ""))
                    note.setPos(item_data.get("pos_x",0), item_data.get("pos_y",0))
                    if "width" in item_data and "height" in item_data:
                        note.document().setTextWidth(item_data["width"] - 2 * note.document().documentMargin())
                        note._user_has_resized = True
                        note._update_wrap_mode_based_on_state()
                    self.scene.addItem(note)
                elif item_type == "pen_stroke":
                    stroke = PenStrokeItem(); path_obj = QPainterPath()
                    for pt_data in item_data.get("points", []):
                        if pt_data.get("type_val") == int(QPainterPath.ElementType.MoveToElement): path_obj.moveTo(float(pt_data.get("x", 0)), float(pt_data.get("y", 0)))
                        elif pt_data.get("type_val") == int(QPainterPath.ElementType.LineToElement): path_obj.lineTo(float(pt_data.get("x", 0)), float(pt_data.get("y", 0)))
                    stroke.setPath(path_obj); self.scene.addItem(stroke)

            self.current_file_path = path
            self.setWindowTitle(f"{WINDOW_TITLE} - {path}")

            # Recalculate everything
            for node in nodes_to_process: self.scene.update_node_dependencies(node)
            for node in nodes_to_process: node.update_node()

        except Exception as e:
            print(f"Error opening file: {e}")

    def save_file(self):
        if self.current_file_path: self.perform_save(self.current_file_path)
        else: self.save_as_file()

    def save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Cosmic Scratchpad File", "", "Cosmic Files (*.cosmic);;All Files (*)")
        if path: self.perform_save(path); self.current_file_path = path; self.setWindowTitle(f"{WINDOW_TITLE} - {path}")

    def get_focused_text_item(self) -> 'QGraphicsTextItem | None':
        focused_item = self.scene.focusItem()
        return focused_item if isinstance(focused_item, ResizableTextItem) else None

    def edit_undo(self):
        item = self.get_focused_text_item()
        if item: item.document().undo()

    def edit_redo(self):
        item = self.get_focused_text_item()
        if item: item.document().redo()

    def edit_cut(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable:
            item.cut()
            if isinstance(item, CalculationNode): item.update_node()

    def edit_copy(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByMouse:
            item.copy()

    def edit_paste(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable:
            item.paste()
            if isinstance(item, CalculationNode): item.update_node()

    def edit_delete_selected(self):
        focused_item = self.get_focused_text_item()
        if focused_item and focused_item.textCursor().hasSelection():
            focused_item.textCursor().removeSelectedText()
            if isinstance(focused_item, CalculationNode): focused_item.update_node()
        else:
            self.scene.keyPressEvent(QKeySequence(QKeySequence.StandardKey.Delete))

    def perform_save(self, path):
        data = {"version": "0.3", "base": self.scene.calculator.base, "nodes": [], "drawing_items": []}
        for item in self.scene.items():
            if isinstance(item, CalculationNode):
                data["nodes"].append({
                    "type": "calculation", "expression": item.expression_str,
                    "pos_x": item.pos().x(), "pos_y": item.pos().y(),
                    "width": item.boundingRect().width(), "height": item.boundingRect().height()
                })
            elif isinstance(item, LineItem):
                line = item.line()
                data["drawing_items"].append({"type": "line", "x1": line.x1(), "y1": line.y1(), "x2": line.x2(), "y2": line.y2()})
            elif isinstance(item, TextNoteItem):
                data["drawing_items"].append({
                    "type": "text_note", "text": item.toPlainText(),
                    "pos_x": item.pos().x(), "pos_y": item.pos().y(),
                    "width": item.boundingRect().width(), "height": item.boundingRect().height()
                })
            elif isinstance(item, PenStrokeItem):
                points = []
                for i in range(item.path().elementCount()):
                    el = item.path().elementAt(i)
                    points.append({"x": el.x, "y": el.y, "type_val": int(el.type)})
                data["drawing_items"].append({"type": "pen_stroke", "points": points})
        try:
            with open(path, 'w') as f: json.dump(data, f, indent=2)
        except Exception as e: print(f"Error saving file: {e}")

# Monkey-patching for compatibility - RESTORED
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

if __name__ == '__main__':
    # Use setattr to avoid direct attribute assignment issues - RESTORED
    setattr(AoP_Calculator, '_rpn_from_expression', rpn_from_expression)
    setattr(AoP_Calculator, '_evaluate_rpn', evaluate_rpn_only)
    app = QApplication(sys.argv)
    window = CosmicScratchpadWindow()
    window.show()
    sys.exit(app.exec())
