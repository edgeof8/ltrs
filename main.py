import sys
from pathlib import Path

# --- Add project root to sys.path ---
# This allows the script to be run directly and find the aopl_python_impl module.
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
# ------------------------------------

# main.py
import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenuBar, QFileDialog, QToolBar, QButtonGroup,
                               QGraphicsView, QStatusBar, QGraphicsTextItem, QGraphicsRectItem, QGraphicsItem)
from PySide6.QtGui import QBrush, QPainter, QIntValidator, QKeySequence, QColor, QPainterPath, QAction, QPen, QTransform, QFont
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from aopl_python_impl.aop_calculator import AoP_Calculator
from cosmic_scene import CosmicScene
from io_manager import IOManager
from gui_items.calculation_node import CalculationNode
from gui_items.text_note_item import TextNoteItem
from gui_items.line_item import LineItem
from gui_items.pen_stroke_item import PenStrokeItem
from gui_items.base_item import ResizableTextItem
from gui_items.plot_node import PlotNode
from config import (WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BACKGROUND,
                    COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT, COLOR_TEXT_RESULT,
                    DrawingToolMode)
import os
import importlib
import sys
from pathlib import Path

def load_plugins(scene):
    """
    Loads plugins from the plugins/ directory and registers their commands into the scene's command_handlers.
    """
    plugins_dir = Path(__file__).parent / "plugins"
    if not plugins_dir.exists():
        print(f"Plugins directory {plugins_dir} not found. Skipping plugin loading.")
        return

    sys.path.append(str(plugins_dir))
    loaded_commands = 0

    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name.startswith("__"):
            continue
        plugin_name = plugin_file.stem
        try:
            plugin_module = importlib.import_module(plugin_name)
            if hasattr(plugin_module, "register"):
                plugin_commands = plugin_module.register()
                if isinstance(plugin_commands, dict):
                    for cmd, handler in plugin_commands.items():
                        if cmd in scene.command_handlers:
                            print(f"Warning: Plugin {plugin_name} overwrites existing command {cmd}")
                        scene.command_handlers[cmd] = handler
                        loaded_commands += 1
                    print(f"Loaded plugin {plugin_name} with commands: {list(plugin_commands.keys())}")
                else:
                    print(f"Error: Plugin {plugin_name} register() did not return a dictionary.")
            else:
                print(f"Error: Plugin {plugin_name} has no register() function.")
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")

    sys.path.remove(str(plugins_dir))
    print(f"Plugin loading complete. Loaded {loaded_commands} commands from {len(list(plugins_dir.glob('*.py')))} plugin files.")

class GroupBoundingBox(QGraphicsRectItem):
    def __init__(self, scene, selected_items, parent=None):
        self.selected_items = selected_items
        bounding_rect = self.calculate_bounding_rect()
        super().__init__(bounding_rect, parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setPen(QPen(QColor(COLOR_TEXT_RESULT), 1, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.resize_handles = []
        self._resize_handle_size = 8.0
        self._is_resizing = False
        self._resize_handle_active = None
        self._original_mouse_pos_scene = QPointF()
        self._original_rect_scene = QRectF()
        self.create_resize_handles()

    def calculate_bounding_rect(self):
        if not self.selected_items:
            return QRectF(0, 0, 0, 0)
        rect = self.selected_items[0].sceneBoundingRect()
        for item in self.selected_items[1:]:
            rect = rect.united(item.sceneBoundingRect())
        return rect.adjusted(-10, -10, 10, 10)

    def create_resize_handles(self):
        rect = self.rect()
        s = self._resize_handle_size
        handle_positions = {
            "top_left": QRectF(rect.left(), rect.top(), s, s),
            "top_right": QRectF(rect.right() - s, rect.top(), s, s),
            "bottom_left": QRectF(rect.left(), rect.bottom() - s, s, s),
            "bottom_right": QRectF(rect.right() - s, rect.bottom() - s, s, s)
        }
        for name, handle_rect in handle_positions.items():
            handle = QGraphicsRectItem(handle_rect, self)
            handle.setBrush(QBrush(COLOR_TEXT_RESULT))
            handle.setPen(Qt.PenStyle.NoPen)
            self.resize_handles.append((name, handle))

    def update_resize_handles(self):
        rect = self.rect()
        s = self._resize_handle_size
        handle_positions = {
            "top_left": QRectF(rect.left(), rect.top(), s, s),
            "top_right": QRectF(rect.right() - s, rect.top(), s, s),
            "bottom_left": QRectF(rect.left(), rect.bottom() - s, s, s),
            "bottom_right": QRectF(rect.right() - s, rect.bottom() - s, s, s)
        }
        for name, handle in self.resize_handles:
            handle.setRect(handle_positions[name])

    def mousePressEvent(self, event):
        pos_in_item = event.pos()
        for name, handle in self.resize_handles:
            if handle.rect().contains(pos_in_item):
                self._is_resizing = True
                self._resize_handle_active = name
                self._original_mouse_pos_scene = event.scenePos()
                self._original_rect_scene = self.sceneBoundingRect()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing and self._resize_handle_active:
            delta_scene = event.scenePos() - self._original_mouse_pos_scene
            new_scene_rect = QRectF(self._original_rect_scene)
            handle = self._resize_handle_active
            if "bottom" in handle:
                new_scene_rect.setBottom(self._original_rect_scene.bottom() + delta_scene.y())
            if "right" in handle:
                new_scene_rect.setRight(self._original_rect_scene.right() + delta_scene.x())
            if "top" in handle:
                new_scene_rect.setTop(self._original_rect_scene.top() + delta_scene.y())
            if "left" in handle:
                new_scene_rect.setLeft(self._original_rect_scene.left() + delta_scene.x())
            if new_scene_rect.width() < 20:
                if "left" in handle:
                    new_scene_rect.setLeft(new_scene_rect.right() - 20)
                else:
                    new_scene_rect.setWidth(20)
            if new_scene_rect.height() < 20:
                if "top" in handle:
                    new_scene_rect.setTop(new_scene_rect.bottom() - 20)
                else:
                    new_scene_rect.setHeight(20)
            self.setRect(new_scene_rect)
            self.update_resize_handles()
            self.apply_scaling(new_scene_rect)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_handle_active = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def apply_scaling(self, new_rect):
        original_rect = self._original_rect_scene
        scale_x = new_rect.width() / original_rect.width() if original_rect.width() != 0 else 1
        scale_y = new_rect.height() / original_rect.height() if original_rect.height() != 0 else 1
        anchor = original_rect.center()
        for item in self.selected_items:
            item_rect = item.sceneBoundingRect()
            transform = QTransform()
            transform.translate(anchor.x(), anchor.y())
            transform.scale(scale_x, scale_y)
            transform.translate(-anchor.x(), -anchor.y())
            new_pos = transform.map(item.pos())
            item.setPos(new_pos)
            if isinstance(item, ResizableTextItem):
                new_font_size = item._original_font_size * scale_y
                font = QFont(item.font().family(), int(new_font_size))
                item.setFont(font)
                item.current_font_size = int(new_font_size)
                item.document().adjustSize()
                item.prepareGeometryChange()
                item.update()

class CosmicView(QGraphicsView):
    scenePosChanged = Signal(QPointF)
    zoomChanged = Signal(float)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.panning = False
        self.group_bounding_box = None
        self.scene().selectionChanged.connect(self.update_group_bounding_box)

    def update_group_bounding_box(self):
        selected_items = self.scene().selectedItems()
        if len(selected_items) > 1:
            if self.group_bounding_box:
                if self.group_bounding_box in self.scene().items():
                    self.scene().removeItem(self.group_bounding_box)
            self.group_bounding_box = GroupBoundingBox(self.scene(), selected_items)
            self.scene().addItem(self.group_bounding_box)
        else:
            if self.group_bounding_box and self.group_bounding_box in self.scene().items():
                self.scene().removeItem(self.group_bounding_box)
            self.group_bounding_box = None

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
            self.scale(zoom_factor, zoom_factor)
            self.zoomChanged.emit(self.transform().m11())
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        is_panning_key = event.button() == Qt.MouseButton.MiddleButton or \
                         (event.button() == Qt.MouseButton.LeftButton and QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)

        if is_panning_key:
            self.panning = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # FIX: Use event.position() instead of event.pos()
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
        load_plugins(self.scene)
        self.view = CosmicView(self.scene, self)
        self.scene.window = self
        self.current_drawing_tool = DrawingToolMode.CALCULATE

        self.io_manager = IOManager(self)

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
                self.tool_button_group.addButton(button) # type: ignore

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
        open_action = QAction("&Open...", self); open_action.setShortcut(QKeySequence.StandardKey.Open); open_action.triggered.connect(self.io_manager.open_file)
        save_action = QAction("&Save", self); save_action.setShortcut(QKeySequence.StandardKey.Save); save_action.triggered.connect(self.io_manager.save_file)
        save_as_action = QAction("Save &As...", self); save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs); save_as_action.triggered.connect(self.io_manager.save_as_file)
        export_action = QAction("Export as Python Script...", self); export_action.triggered.connect(self.io_manager.export_as_python_script)
        share_action = QAction("Share to Cosmic Library...", self); share_action.triggered.connect(self.io_manager.share_to_library)
        browse_action = QAction("Browse Cosmic Library...", self); browse_action.triggered.connect(self.browse_library)
        exit_action = QAction("E&xit", self); exit_action.setShortcut(QKeySequence.StandardKey.Quit); exit_action.triggered.connect(self.close)
        file_menu.addAction(new_action); file_menu.addAction(open_action); file_menu.addAction(save_action); file_menu.addAction(save_as_action); file_menu.addAction(export_action); file_menu.addSeparator(); file_menu.addAction(exit_action)
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
        self.scene.calculator = AoP_Calculator(base=10)
        self.scene.node_definitions = {}
        self.scene.dependencies = {}
        self.base_input.setText("10")
        self.current_file_path = None
        self.setWindowTitle(WINDOW_TITLE)

    def browse_library(self):
        from library_browser import LibraryBrowserDialog
        dialog = LibraryBrowserDialog(self)
        dialog.exec()

    def get_focused_text_item(self) -> 'QGraphicsTextItem | None':
        focused_item = self.scene.focusItem()
        return focused_item if isinstance(focused_item, ResizableTextItem) else None # type: ignore

    def edit_undo(self):
        item = self.get_focused_text_item()
        if item: item.document().undo()

    def edit_redo(self):
        item = self.get_focused_text_item()
        if item: item.document().redo()

    def edit_cut(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable:
            item.cut() # type: ignore
            if isinstance(item, CalculationNode): item.update_node_and_propagate()

    def edit_copy(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByMouse:
            item.copy() # type: ignore

    def edit_paste(self):
        item = self.get_focused_text_item()
        if item and item.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable:
            item.paste() # type: ignore
            if isinstance(item, CalculationNode): item.update_node_and_propagate()

    def edit_delete_selected(self):
        focused_item = self.get_focused_text_item()
        if focused_item and focused_item.textCursor().hasSelection():
            focused_item.textCursor().removeSelectedText()
            if isinstance(focused_item, CalculationNode): focused_item.update_node_and_propagate()
        else:
            self.scene.keyPressEvent(QKeySequence(QKeySequence.StandardKey.Delete))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CosmicScratchpadWindow()
    window.show()
    sys.exit(app.exec())

