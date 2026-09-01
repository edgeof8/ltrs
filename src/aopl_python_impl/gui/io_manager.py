import json
import os
import sys
import tempfile
from pathlib import Path
from PySide6.QtWidgets import (QFileDialog, QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QTextEdit, QPushButton)
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import QPointF, QRectF, Qt

# Assuming these are needed by the moved methods
from .gui_items.calculation_node import CalculationNode
from .gui_items.text_note_item import TextNoteItem
from .gui_items.line_item import LineItem
from .gui_items.pen_stroke_item import PenStrokeItem
from .gui_items.base_item import ResizableTextItem
from aopl_python_impl.aop_calculator import AoP_Calculator
# from .cosmic_scene import CosmicScene # Avoid circular import, IOManager receives window which has scene
from .config import WINDOW_TITLE # Assuming WINDOW_TITLE is needed for window title updates
from .dialogs import ShareDialog


def _examples_dir():
    repo_root = Path(__file__).resolve().parents[3]
    path = repo_root / "examples"
    return path if path.is_dir() else None

class IOManager:
    def __init__(self, window):
        self.window = window # The QMainWindow instance

    def load_scene_from_data(self, data):
        self.window.new_file() # Assuming new_file should still be called on the window
        self.window.scene.calculator.base = data.get("base", 10)
        self.window.base_input.setText(str(self.window.scene.calculator.base))
        nodes_to_process = []
        for node_data in data.get("nodes", []):
            node = CalculationNode(self.window.scene, self.window.scene.calculator)
            expr = node_data.get("expression", "")
            node.expression_str = expr
            node.output_mode = node_data.get("output_mode", "num")
            node.setPlainText(expr)
            node.setPos(node_data.get("pos_x", 0), node_data.get("pos_y", 0))
            # Restore size if saved
            if "width" in node_data and "height" in node_data:
                node.document().setTextWidth(node_data["width"] - 2 * node.document().documentMargin())
                node._user_has_resized = True
                node._update_wrap_mode_based_on_state()
            self.window.scene.addItem(node)
            nodes_to_process.append(node)

        for item_data in data.get("drawing_items", []):
            item_type = item_data.get("type")
            if item_type == "line": self.window.scene.addItem(LineItem(item_data.get("x1",0), item_data.get("y1",0), item_data.get("x2",0), item_data.get("y2",0)))
            elif item_type == "text_note":
                note = TextNoteItem(item_data.get("text", ""))
                note.setPos(item_data.get("pos_x",0), item_data.get("pos_y",0))
                if "width" in item_data and "height" in item_data:
                    note.document().setTextWidth(item_data["width"] - 2 * note.document().documentMargin())
                    note._user_has_resized = True
                    note._update_wrap_mode_based_on_state()
                self.window.scene.addItem(note)
            elif item_type == "pen_stroke":
                stroke = PenStrokeItem(); path_obj = QPainterPath()
                for pt_data in item_data.get("points", []):
                    type_val = pt_data.get("type_val")
                    if type_val is not None:
                        element_type = QPainterPath.ElementType(type_val)
                        if element_type == QPainterPath.ElementType.MoveToElement: path_obj.moveTo(float(pt_data.get("x", 0)), float(pt_data.get("y", 0)))
                        elif element_type == QPainterPath.ElementType.LineToElement: path_obj.lineTo(float(pt_data.get("x", 0)), float(pt_data.get("y", 0)))
                stroke.setPath(path_obj); self.window.scene.addItem(stroke)

        self.window.current_file_path = None
        self.window.setWindowTitle(f"{WINDOW_TITLE} - [Downloaded Scratchpad]")

        # Recalculate everything
        for node in nodes_to_process: self.window.scene.update_and_propagate(node)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Open Cosmic Scratchpad File",
            str(_examples_dir()) if _examples_dir() else "",
            "Cosmic Files (*.cosmic);;All Files (*)",
        )
        if not path: return
        try:
            with open(path, 'r') as f: data = json.load(f)
            self.window.new_file() # Assuming new_file should still be called on the window
            self.window.scene.calculator.base = data.get("base", 10)
            self.window.base_input.setText(str(self.window.scene.calculator.base))
            nodes_to_process = []
            for node_data in data.get("nodes", []):
                node = CalculationNode(self.window.scene, self.window.scene.calculator)
                expr = node_data.get("expression", "")
                node.expression_str = expr
                node.output_mode = node_data.get("output_mode", "num")
                node.setPlainText(expr)
                node.setPos(node_data.get("pos_x", 0), node_data.get("pos_y", 0))
                # Restore size if saved
                if "width" in node_data and "height" in node_data:
                    node.document().setTextWidth(node_data["width"] - 2 * node.document().documentMargin())
                    node._user_has_resized = True
                    node._update_wrap_mode_based_on_state()
                self.window.scene.addItem(node)
                nodes_to_process.append(node)

            for item_data in data.get("drawing_items", []):
                item_type = item_data.get("type")
                if item_type == "line": self.window.scene.addItem(LineItem(item_data.get("x1",0), item_data.get("y1",0), item_data.get("x2",0), item_data.get("y2",0)))
                elif item_type == "text_note":
                    note = TextNoteItem(item_data.get("text", ""))
                    note.setPos(item_data.get("pos_x",0), item_data.get("pos_y",0))
                    if "width" in item_data and "height" in item_data:
                        note.document().setTextWidth(item_data["width"] - 2 * note.document().documentMargin())
                        note._user_has_resized = True
                        note._update_wrap_mode_based_on_state()
                    self.window.scene.addItem(note)
                elif item_type == "pen_stroke":
                    stroke = PenStrokeItem(); path_obj = QPainterPath()
                for pt_data in item_data.get("points", []):
                    type_val = pt_data.get("type_val")
                    if type_val is not None:
                        element_type = QPainterPath.ElementType(type_val)
                        if element_type == QPainterPath.ElementType.MoveToElement: path_obj.moveTo(float(pt_data.get("x", 0)), float(pt_data.get("y", 0)))
                        elif element_type == QPainterPath.ElementType.LineToElement: path_obj.lineTo(float(pt_data.get("x", 0)), float(pt_data.get("y", 0)))
                    stroke.setPath(path_obj); self.window.scene.addItem(stroke)

            self.window.current_file_path = path
            self.window.setWindowTitle(f"{WINDOW_TITLE} - {path}")

            # Recalculate everything
            for node in nodes_to_process: self.window.scene.update_and_propagate(node)


        except Exception as e:
            print(f"Error opening file: {e}")

    def save_file(self):
        if self.window.current_file_path: self.perform_save(self.window.current_file_path)
        else: self.save_as_file()

    def save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(self.window, "Save Cosmic Scratchpad File", "", "Cosmic Files (*.cosmic);;All Files (*)")
        if path: self.perform_save(path); self.window.current_file_path = path; self.window.setWindowTitle(f"{WINDOW_TITLE} - {path}")

    def perform_save(self, path):
        data = {"version": "0.3", "base": self.window.scene.calculator.base, "nodes": [], "drawing_items": []}
        for item in self.window.scene.items():
            if isinstance(item, CalculationNode):
                data["nodes"].append({
                    "type": "calculation", "expression": item.expression_str, # type: ignore
                    "output_mode": getattr(item, "output_mode", "num"),
                    "pos_x": item.pos().x(), "pos_y": item.pos().y(),
                    "width": item.boundingRect().width(), "height": item.boundingRect().height()
                })
            elif isinstance(item, LineItem):
                line = item.line() # type: ignore
                data["drawing_items"].append({"type": "line", "x1": line.x1(), "y1": line.y1(), "x2": line.x2(), "y2": line.y2()})
            elif isinstance(item, TextNoteItem):
                data["drawing_items"].append({
                    "type": "text_note", "text": item.toPlainText(), # type: ignore
                    "pos_x": item.pos().x(), "pos_y": item.pos().y(),
                    "width": item.boundingRect().width(), "height": item.boundingRect().height()
                })
            elif isinstance(item, PenStrokeItem):
                points = []
                for i in range(item.path().elementCount()): # type: ignore
                    el = item.path().elementAt(i) # type: ignore
                    points.append({"x": el.x, "y": el.y, "type_val": int(el.type)})  # type: ignore
                data["drawing_items"].append({"type": "pen_stroke", "points": points})
        try:
            with open(path, 'w') as f: json.dump(data, f, indent=2)
        except Exception as e: print(f"Error saving file: {e}")

    def export_as_python_script(self):
        path, _ = QFileDialog.getSaveFileName(self.window, "Export as Python Script", "", "Python Files (*.py);;All Files (*)")
        if path:
            script_content = self.window.scene.generate_python_script() # Assuming generate_python_script is on the scene
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                self.window.status_bar.showMessage(f"Exported script to {path}", 5000) # Assuming status_bar is on the window
            except Exception as e:
                self.window.status_bar.showMessage(f"Error exporting script: {e}", 5000) # Assuming status_bar is on the window

    def share_to_library(self):
        # This method contains an inner class and imports, which is not ideal.
        # For simplicity in moving, I'll keep it as is for now, but it could be refactored further.
        try:
            import requests
        except ImportError:
            self.window.status_bar.showMessage(
                "Share needs the 'explain' extra (pip install -e \".[explain]\").", 5000)
            return
        import tempfile
        import json

        dialog = ShareDialog(self.window) # Pass the main window as parent
        if dialog.exec():
            title = dialog.title_input.text()
            author = dialog.author_input.text()
            description = dialog.desc_input.toPlainText()

            if not title or not author:
                self.window.status_bar.showMessage("Error: Title and Author are required.", 5000) # Assuming status_bar is on the window
                return

            # Prepare the scratchpad data
            data = {"version": "0.3", "base": self.window.scene.calculator.base, "nodes": [], "drawing_items": []}
            for item in self.window.scene.items():
                if isinstance(item, CalculationNode):
                    data["nodes"].append({
                        "type": "calculation", "expression": item.expression_str, # type: ignore
                        "output_mode": getattr(item, "output_mode", "num"),
                        "pos_x": item.pos().x(), "pos_y": item.pos().y(),
                        "width": item.boundingRect().width(), "height": item.boundingRect().height()
                    })
                elif isinstance(item, LineItem):
                    line = item.line() # type: ignore
                    data["drawing_items"].append({"type": "line", "x1": line.x1(), "y1": line.y1(), "x2": line.x2(), "y2": line.y2()})
                elif isinstance(item, TextNoteItem):
                    data["drawing_items"].append({
                        "type": "text_note", "text": item.toPlainText(), # type: ignore
                        "pos_x": item.pos().x(), "pos_y": item.pos().y(),
                        "width": item.boundingRect().width(), "height": item.boundingRect().height()
                    })
                elif isinstance(item, PenStrokeItem):
                    points = []
                    for i in range(item.path().elementCount()): # type: ignore
                        el = item.path().elementAt(i) # type: ignore
                        points.append({"x": el.x, "y": el.y, "type_val": int(el.type)})  # type: ignore
                    data["drawing_items"].append({"type": "pen_stroke", "points": points})

            try:
                # Create a temporary file to store the scratchpad data
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cosmic') as temp_file:
                    json.dump(data, temp_file, indent=2)
                    temp_file_path = temp_file.name

                # Upload to the server
                with open(temp_file_path, 'rb') as f:
                    files = {'file': f}
                    data = {'title': title, 'author': author, 'description': description}
                    response = requests.post('http://localhost:8000/upload', files=files, data=data)

                # Clean up temporary file
                os.unlink(temp_file_path)

                if response.status_code == 200:
                    self.window.status_bar.showMessage("Successfully shared to Cosmic Library.", 5000) # Assuming status_bar is on the window
                else:
                    self.window.status_bar.showMessage(f"Error sharing to library: {response.text}", 5000) # Assuming status_bar is on the window
            except Exception as e:
                self.window.status_bar.showMessage(f"Error sharing to library: {str(e)}", 5000) # Assuming status_bar is on the window
        else:
            self.window.status_bar.showMessage("Sharing cancelled.", 5000) # Assuming status_bar is on the window
