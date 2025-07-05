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

class ResizableTextItem(QGraphicsTextItem):
    snapped = Signal(str, float)  # Signal for snapping to alignment guides (axis, position)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_resizing = False; self._resize_handle_active = None; self._resize_handle_size = 8.0
        self._original_mouse_pos_scene = QPointF(); self._original_rect_scene = QRectF()
        self._min_node_width = 100.0; self._min_node_height = FONT_SIZE + 16
        self.current_font_size = FONT_SIZE; self._min_font_size = 8; self._user_has_resized = False
        self._original_font_size = FONT_SIZE
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges); self.setAcceptHoverEvents(True)
        opt = QTextOption(self.document().defaultTextOption()); opt.setWrapMode(QTextOption.WrapMode.NoWrap); self.document().setDefaultTextOption(opt); self.setTextWidth(-1)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            if self.scene() and hasattr(self.scene(), '_show_snap_guide'):
                self.snapped.connect(self.scene()._show_snap_guide)  # type: ignore
        return super().itemChange(change, value)

    def _update_wrap_mode_based_on_state(self):
        opt = QTextOption(self.document().defaultTextOption())
        if self._user_has_resized and self.textWidth() > 0: opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        else: opt.setWrapMode(QTextOption.WrapMode.NoWrap); self.setTextWidth(-1)
        self.document().setDefaultTextOption(opt)

    def adjustFontSizeToFitRect(self, target_rect: QRectF | None = None):
        if target_rect is None: target_rect = self.boundingRect()
        if target_rect is None: return
        doc_margin = self.document().documentMargin()
        available_width = target_rect.width() - 2 * doc_margin
        available_height = target_rect.height() - 2 * doc_margin
        if available_width <= 0 or available_height <= 0: return
        current_text = self.toPlainText()
        if not current_text: self.setFont(QFont(FONT_FAMILY, self.current_font_size)); return
        font_size = self.current_font_size; font = QFont(FONT_FAMILY)
        while font_size >= self._min_font_size:
            font.setPixelSize(font_size); metrics = QFontMetrics(font); self.document().setTextWidth(available_width)
            text_rect = metrics.boundingRect(0, 0, int(available_width), 10000, Qt.TextFlag.TextWordWrap, current_text)
            if text_rect.height() <= available_height and text_rect.width() <= available_width: break
            font_size -= 1
        if font_size < self._min_font_size: font_size = self._min_font_size
        final_font = QFont(FONT_FAMILY); final_font.setPixelSize(font_size); self.setFont(final_font); self.current_font_size = font_size
        self.document().setTextWidth(available_width); self.document().adjustSize(); self.prepareGeometryChange(); self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget or QWidget())
        if self.isSelected():
            painter.setBrush(QBrush(QColor(COLOR_TEXT_RESULT).lighter(110))); painter.setPen(Qt.PenStyle.NoPen)
            for handle_rect in self.get_resize_handles_rects().values(): painter.drawEllipse(handle_rect)

    def get_resize_handles_rects(self) -> dict[str, QRectF]:
        rect = self.boundingRect(); s = self._resize_handle_size
        return {"top_left": QRectF(rect.left(), rect.top(), s, s), "top_right": QRectF(rect.right() - s, rect.top(), s, s), "bottom_left": QRectF(rect.left(), rect.bottom() - s, s, s), "bottom_right": QRectF(rect.right() - s, rect.bottom() - s, s, s)}

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.isSelected() and not self._is_resizing:
            # FIX: Use event.pos() which is correct for QGraphicsSceneHoverEvent
            pos_in_item = event.pos()
            handles = self.get_resize_handles_rects()
            if handles["top_left"].contains(pos_in_item) or handles["bottom_right"].contains(pos_in_item): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif handles["top_right"].contains(pos_in_item) or handles["bottom_left"].contains(pos_in_item): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else: self.setCursor(Qt.CursorShape.IBeamCursor)
            return
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.isSelected() and event.button() == Qt.MouseButton.LeftButton:
            # Use event.pos() which is correct for QGraphicsSceneMouseEvent
            pos_in_item = event.pos()
            for handle_name, rect in self.get_resize_handles_rects().items():
                if rect.contains(pos_in_item):
                    self._is_resizing = True; self._resize_handle_active = handle_name; self._original_mouse_pos_scene = event.scenePos(); self._original_rect_scene = self.sceneBoundingRect(); self._original_font_size = self.current_font_size; event.accept(); return
        self._is_resizing = False; super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing and self._resize_handle_active:
            delta_scene = event.scenePos() - self._original_mouse_pos_scene; new_scene_rect = QRectF(self._original_rect_scene)
            handle = self._resize_handle_active
            if "bottom" in handle: new_scene_rect.setBottom(self._original_rect_scene.bottom() + delta_scene.y())
            if "right" in handle: new_scene_rect.setRight(self._original_rect_scene.right() + delta_scene.x())
            if "top" in handle: new_scene_rect.setTop(self._original_rect_scene.top() + delta_scene.y())
            if "left" in handle: new_scene_rect.setLeft(self._original_rect_scene.left() + delta_scene.x())
            if new_scene_rect.width() < self._min_node_width:
                if "left" in handle: new_scene_rect.setLeft(new_scene_rect.right() - self._min_node_width)
                else: new_scene_rect.setWidth(self._min_node_width)
            if new_scene_rect.height() < self._min_node_height:
                if "top" in handle: new_scene_rect.setTop(new_scene_rect.bottom() - self._min_node_height)
                else: new_scene_rect.setHeight(self._min_node_height)
            self.prepareGeometryChange(); self.setPos(new_scene_rect.topLeft()); self.document().setTextWidth(new_scene_rect.width() - 2 * self.document().documentMargin())
            self._user_has_resized = True; self._update_wrap_mode_based_on_state(); self.adjustFontSizeToFitRect(QRectF(0, 0, new_scene_rect.width(), new_scene_rect.height())); event.accept(); return
        elif self.isSelected() and not self._is_resizing and self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
            # Handle snapping to alignment guides
            super().mouseMoveEvent(event)
            self._snap_to_alignment_guides()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def _snap_to_alignment_guides(self):
        if not self.scene():
            return
        tolerance = 5.0
        self_rect = self.sceneBoundingRect()
        self_top = self_rect.top()
        self_center_y = self_rect.center().y()
        self_bottom = self_rect.bottom()
        self_left = self_rect.left()
        self_center_x = self_rect.center().x()
        self_right = self_rect.right()

        snap_x = None
        snap_y = None
        for item in self.scene().items():
            if item == self or not isinstance(item, ResizableTextItem):
                continue
            item_rect = item.sceneBoundingRect()
            item_top = item_rect.top()
            item_center_y = item_rect.center().y()
            item_bottom = item_rect.bottom()
            item_left = item_rect.left()
            item_center_x = item_rect.center().x()
            item_right = item_rect.right()

            # Check horizontal alignments
            if abs(self_top - item_top) < tolerance and (snap_y is None or abs(self_top - item_top) < abs(self_top - snap_y if snap_y is not None else float('inf'))):
                snap_y = item_top
                self.snapped.emit("y", snap_y)
            elif abs(self_center_y - item_center_y) < tolerance and (snap_y is None or abs(self_center_y - item_center_y) < abs(self_top - snap_y if snap_y is not None else float('inf'))):
                snap_y = item_center_y - self_rect.height() / 2
                self.snapped.emit("y", snap_y)
            elif abs(self_bottom - item_bottom) < tolerance and (snap_y is None or abs(self_bottom - item_bottom) < abs(self_top - snap_y if snap_y is not None else float('inf'))):
                snap_y = item_bottom - self_rect.height()
                self.snapped.emit("y", snap_y)

            # Check vertical alignments
            if abs(self_left - item_left) < tolerance and (snap_x is None or abs(self_left - item_left) < abs(self_left - snap_x if snap_x is not None else float('inf'))):
                snap_x = item_left
                self.snapped.emit("x", snap_x)
            elif abs(self_center_x - item_center_x) < tolerance and (snap_x is None or abs(self_center_x - item_center_x) < abs(self_left - snap_x if snap_x is not None else float('inf'))):
                snap_x = item_center_x - self_rect.width() / 2
                self.snapped.emit("x", snap_x)
            elif abs(self_right - item_right) < tolerance and (snap_x is None or abs(self_right - item_right) < abs(self_left - snap_x if snap_x is not None else float('inf'))):
                snap_x = item_right - self_rect.width()
                self.snapped.emit("x", snap_x)

        if snap_x is not None or snap_y is not None:
            new_pos = self.pos()
            if snap_x is not None:
                new_pos.setX(snap_x)
            if snap_y is not None:
                new_pos.setY(snap_y)
            self.setPos(new_pos)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing:
            self._is_resizing = False; self._resize_handle_active = None; self._user_has_resized = True
            self._update_wrap_mode_based_on_state(); self.adjustFontSizeToFitRect(self.boundingRect()); self.document().adjustSize(); self.prepareGeometryChange(); self.unsetCursor(); event.accept(); return
        super().mouseReleaseEvent(event)
