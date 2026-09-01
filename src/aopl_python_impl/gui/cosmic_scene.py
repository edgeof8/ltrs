from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsScene, QToolBar, QMenu, QInputDialog, QGraphicsLineItem
from PySide6.QtGui import QPainterPath, QAction, QPen
from PySide6.QtCore import Qt
from aopl_python_impl.aop_calculator import AoP_Calculator
from .config import DrawingToolMode, COLOR_VAR_EDGE
from .command_handler import CommandHandler
from .dependency_manager import DependencyGraphManager
from .evaluation_manager import EvaluationManager
from .gui_items.calculation_node import CalculationNode
from .gui_items.line_item import LineItem
from .gui_items.text_note_item import TextNoteItem
from .gui_items.pen_stroke_item import PenStrokeItem
from .gui_items.base_item import ResizableTextItem
from .gui_items.plot_node import PlotNode
from .canvas_history import CanvasHistory

if TYPE_CHECKING:
    from .app import CosmicScratchpadWindow

if TYPE_CHECKING:
    from .app import CosmicScratchpadWindow

class CosmicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calculator = AoP_Calculator(base=10) # Removed load_default_vars
        self.graph_manager = DependencyGraphManager()
        self.evaluation_manager = EvaluationManager(self)
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
        self.command_handler = CommandHandler(self)
        # Plugins and EvaluationManager dispatch through this dict.
        self.command_handlers = self.command_handler.command_handlers
        self.var_edge_items: list = []
        self.history = CanvasHistory(self.serialize_canvas, self.restore_canvas)
        self.history.push()


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

        if isinstance(item_at_click, CalculationNode):
            mode = item_at_click.output_mode
            other = "aop" if mode == "num" else "num"
            toggle = QAction(f"Output mode: {mode} (switch to {other})", menu)
            toggle.triggered.connect(item_at_click.toggle_output_mode)
            menu.addAction(toggle)
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
                    if item.defined_variable and item.defined_variable in self.graph_manager.dependencies: # type: ignore
                        dependents = list(self.graph_manager.dependencies[item.defined_variable]) # type: ignore
                        for dep_node in dependents:
                            if isinstance(dep_node, CalculationNode):
                                dep_node.update_node_and_propagate() # Re-evaluate to show error
                    # Remove the variable from the calculator and our tracking
                    if item.defined_variable in self.calculator.variables: # type: ignore
                        del self.calculator.variables[item.defined_variable] # type: ignore
                    if item in self.graph_manager.node_definitions:
                        del self.graph_manager.node_definitions[item]

                self.removeItem(item)
            return
        super().keyPressEvent(event)

    def update_and_propagate(self, start_node, propagate: bool = True):
        self.graph_manager.update_dependencies_for_node(start_node)
        self.evaluation_manager.process_node_update(start_node, propagate)
        self.refresh_var_edges()
        self.history.push()


    def serialize_canvas(self) -> dict:
        data = {"version": "0.4", "base": self.calculator.base, "nodes": [], "drawing_items": []}
        for item in self.items():
            if isinstance(item, CalculationNode):
                data["nodes"].append({
                    "type": "calculation",
                    "expression": item.expression_str,
                    "output_mode": item.output_mode,
                    "pos_x": item.pos().x(),
                    "pos_y": item.pos().y(),
                    "width": item.boundingRect().width(),
                    "height": item.boundingRect().height(),
                })
            elif isinstance(item, LineItem):
                line = item.line()
                data["drawing_items"].append({
                    "type": "line", "x1": line.x1(), "y1": line.y1(), "x2": line.x2(), "y2": line.y2(),
                })
            elif isinstance(item, TextNoteItem):
                data["drawing_items"].append({
                    "type": "text_note", "text": item.toPlainText(),
                    "pos_x": item.pos().x(), "pos_y": item.pos().y(),
                    "width": item.boundingRect().width(), "height": item.boundingRect().height(),
                })
            elif isinstance(item, PenStrokeItem):
                points = []
                for i in range(item.path().elementCount()):
                    el = item.path().elementAt(i)
                    points.append({"x": el.x, "y": el.y, "type_val": int(el.type)})
                data["drawing_items"].append({"type": "pen_stroke", "points": points})
        return data

    def restore_canvas(self, data: dict) -> None:
        for item in list(self.items()):
            self.removeItem(item)
        self.var_edge_items = []
        self.graph_manager.clear()
        self.calculator = AoP_Calculator(base=data.get("base", 10))
        self.calculator.variables.clear()
        nodes = []
        for node_data in data.get("nodes", []):
            node = CalculationNode(self, self.calculator)
            expr = node_data.get("expression", "")
            node.expression_str = expr
            node.output_mode = node_data.get("output_mode", "num")
            node.setPlainText(expr)
            node.setPos(node_data.get("pos_x", 0), node_data.get("pos_y", 0))
            self.addItem(node)
            nodes.append(node)
        for node in nodes:
            self.graph_manager.update_dependencies_for_node(node)
        for node in nodes:
            self.evaluation_manager.process_node_update(node, propagate=False)
        self.refresh_var_edges()

    def refresh_var_edges(self) -> None:
        for line in self.var_edge_items:
            if line.scene() is self:
                self.removeItem(line)
        self.var_edge_items = []
        pen = QPen(COLOR_VAR_EDGE, 1.2, Qt.PenStyle.DashLine)
        for src, dst in self.graph_manager.definition_edges():
            c1 = src.sceneBoundingRect().center()
            c2 = dst.sceneBoundingRect().center()
            line = QGraphicsLineItem(c1.x(), c1.y(), c2.x(), c2.y())
            line.setPen(pen)
            line.setZValue(-1)
            self.addItem(line)
            self.var_edge_items.append(line)


    # Method update_node_dependencies moved to DependencyGraphManager

    # Method evaluate_script moved to EvaluationManager

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
        var_to_def_node = {v: k for k, v in self.graph_manager.node_definitions.items()}

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
