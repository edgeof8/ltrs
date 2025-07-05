from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsItem
from PySide6.QtGui import QPen
from PySide6.QtCore import Qt
from config import DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH

class LineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        pen = QPen(DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH); pen.setCapStyle(Qt.PenCapStyle.RoundCap); self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
