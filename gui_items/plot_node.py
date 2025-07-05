from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QFont, QColor, QBrush, QPainter, QPixmap, QPen
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent
from config import FONT_FAMILY, FONT_SIZE, COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT, COLOR_TEXT_RESULT
import matplotlib.pyplot as plt
import numpy as np
import io
from aopl_python_impl.aop_calculator import AoP_Calculator
from plot_utils import generate_plot_pixmap

if TYPE_CHECKING:
    from cosmic_scene import CosmicScene

class PlotNode(QGraphicsItem):
    def __init__(self, scene, calculator, expression, variable, start_val, end_val, steps=200, log_x=False, log_y=False, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.calculator = calculator
        self.expression = expression
        self.variable = variable
        self.start_val = start_val
        self.end_val = end_val
        self.steps = steps
        self.log_x = log_x
        self.log_y = log_y
        self.pixmap = None
        self.width = 400
        self.height = 300
        self.defined_variable: str | None = None
        self.dependencies = set()
        self._is_resizing = False
        self._resize_handle_active = None
        self._resize_handle_size = 8.0
        self._original_mouse_pos_scene = QPointF()
        self._original_rect_scene = QRectF()
        self._min_width = 200
        self._min_height = 150
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.redraw_plot()

    def scene(self) -> 'CosmicScene':
        return super().scene()  # type: ignore

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        if self.pixmap:
            painter.drawPixmap(10, 30, self.pixmap)
        painter.setPen(QPen(COLOR_TEXT_INPUT))
        painter.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        painter.drawText(10, 20, f"Plot: {self.expression} for {self.variable}")
        if self.isSelected():
            painter.setBrush(QBrush(QColor(COLOR_TEXT_RESULT).lighter(110)))
            painter.setPen(Qt.PenStyle.NoPen)
            for handle_rect in self.get_resize_handles_rects().values():
                painter.drawEllipse(handle_rect)

    def get_resize_handles_rects(self) -> dict[str, QRectF]:
        rect = self.boundingRect()
        s = self._resize_handle_size
        return {
            "top_left": QRectF(rect.left(), rect.top(), s, s),
            "top_right": QRectF(rect.right() - s, rect.top(), s, s),
            "bottom_left": QRectF(rect.left(), rect.bottom() - s, s, s),
            "bottom_right": QRectF(rect.right() - s, rect.bottom() - s, s, s)
        }

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.isSelected() and not self._is_resizing:
            pos_in_item = event.pos()
            handles = self.get_resize_handles_rects()
            if handles["top_left"].contains(pos_in_item) or handles["bottom_right"].contains(pos_in_item):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif handles["top_right"].contains(pos_in_item) or handles["bottom_left"].contains(pos_in_item):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.isSelected() and event.button() == Qt.MouseButton.LeftButton:
            pos_in_item = event.pos()
            for handle_name, rect in self.get_resize_handles_rects().items():
                if rect.contains(pos_in_item):
                    self._is_resizing = True
                    self._resize_handle_active = handle_name
                    self._original_mouse_pos_scene = event.scenePos()
                    self._original_rect_scene = self.sceneBoundingRect()
                    event.accept()
                    return
        self._is_resizing = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing and self._resize_handle_active:
            delta_scene = event.scenePos() - self._original_mouse_pos_scene
            new_scene_rect = QRectF(self._original_rect_scene)
            handle = self._resize_handle_active
            if "bottom" in handle:
                new_scene_rect.setBottom(self._original_rect_scene.bottom() + delta_scene.y())
            if "right" in handle:
                new_scene_rect.setRight(self._original_rect_scene.right() + delta_scene.x())
            if "top" in handle:
                new_scene_rect.setTop(new_scene_rect.bottom() - self._min_height)
            if "left" in handle:
                new_scene_rect.setLeft(new_scene_rect.right() - self._min_width)
            if new_scene_rect.width() < self._min_width:
                if "left" in handle:
                    new_scene_rect.setLeft(new_scene_rect.right() - self._min_width)
                else:
                    new_scene_rect.setWidth(self._min_width)
            if new_scene_rect.height() < self._min_height:
                if "top" in handle:
                    new_scene_rect.setTop(new_scene_rect.bottom() - self._min_height)
                else:
                    new_scene_rect.setHeight(self._min_height)
            self.prepareGeometryChange()
            self.setPos(new_scene_rect.topLeft())
            self.width = new_scene_rect.width()
            self.height = new_scene_rect.height()
            self.redraw_plot()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_handle_active = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def redraw_plot(self):
        self.pixmap = generate_plot_pixmap(
            self.calculator,
            self.expression,
            self.variable,
            self.start_val,
            self.end_val,
            self.steps,
            self.log_x,
            self.log_y,
            int(self.width),
            int(self.height)
        )
        self.prepareGeometryChange()
        self.update()
