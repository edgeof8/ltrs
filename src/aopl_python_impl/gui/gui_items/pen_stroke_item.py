from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen
from PySide6.QtCore import Qt
from ..config import DEFAULT_PEN_COLOR, DEFAULT_PEN_WIDTH

class PenStrokeItem(QGraphicsPathItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        pen = QPen(DEFAULT_PEN_COLOR, DEFAULT_PEN_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin); self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
