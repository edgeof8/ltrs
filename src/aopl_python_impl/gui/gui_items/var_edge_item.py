from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QPainterPath, QBrush, QPolygonF
from PySide6.QtCore import Qt, QPointF
from ..config import COLOR_VAR_EDGE
from ..graph_logic import arrow_head_points, point_on_rect_toward


class VarEdgeItem(QGraphicsPathItem):
    """Dashed arrow from a $var definition node to a node that uses it."""

    def __init__(self, src: QGraphicsItem, dst: QGraphicsItem, parent=None):
        super().__init__(parent)
        self._src = src
        self._dst = dst
        pen = QPen(COLOR_VAR_EDGE, 2.0, Qt.PenStyle.DashLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        self.setBrush(QBrush(COLOR_VAR_EDGE))
        self.setZValue(-1)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.sync()

    def sync(self) -> None:
        r1 = self._src.sceneBoundingRect()
        r2 = self._dst.sceneBoundingRect()
        x1, y1 = point_on_rect_toward(
            r1.center().x(), r1.center().y(), r1.width(), r1.height(),
            r2.center().x(), r2.center().y(),
        )
        x2, y2 = point_on_rect_toward(
            r2.center().x(), r2.center().y(), r2.width(), r2.height(),
            r1.center().x(), r1.center().y(),
        )
        tip, left, right = arrow_head_points(x1, y1, x2, y2)
        path = QPainterPath(QPointF(x1, y1))
        path.lineTo(QPointF(x2, y2))
        path.addPolygon(
            QPolygonF([
                QPointF(*tip),
                QPointF(*left),
                QPointF(*right),
            ])
        )
        self.setPath(path)
