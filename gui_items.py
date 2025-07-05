# gui_items.py
from PySide6.QtWidgets import (QGraphicsTextItem, QApplication, QMenu,
                               QGraphicsLineItem, QGraphicsPathItem, QGraphicsItem,
                               QStyleOptionGraphicsItem, QWidget, QGraphicsSceneMouseEvent,
                               QGraphicsSceneHoverEvent)
from PySide6.QtGui import (QFont, QColor, QBrush, QTextCursor, QPen, QPainterPath, QPainter,
                           QTextOption, QKeyEvent, QFontMetrics)
from PySide6.QtCore import Signal
from PySide6.QtCore import Qt, QRectF, QPointF
from config import (FONT_FAMILY, FONT_SIZE, COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT,
                    COLOR_TEXT_RESULT, COLOR_TEXT_ERROR, DEFAULT_PEN_COLOR,
                    DEFAULT_PEN_WIDTH, DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH,
                    DEFAULT_TEXTNOTE_COLOR)
