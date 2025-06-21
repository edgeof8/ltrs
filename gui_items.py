# gui_items.py
from PySide6.QtWidgets import (QGraphicsTextItem, QApplication, QMenu,
                               QGraphicsLineItem, QGraphicsPathItem, QGraphicsItem,
                               QStyleOptionGraphicsItem, QWidget, QGraphicsSceneMouseEvent,
                               QGraphicsSceneHoverEvent)
from PySide6.QtGui import (QFont, QColor, QBrush, QTextCursor, QPen, QPainterPath, QPainter,
                           QTextOption, QKeyEvent, QFontMetrics)
from PySide6.QtCore import Qt, QRectF, QPointF
from config import (FONT_FAMILY, FONT_SIZE, COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT,
                    COLOR_TEXT_RESULT, COLOR_TEXT_ERROR, DEFAULT_PEN_COLOR,
                    DEFAULT_PEN_WIDTH, DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH,
                    DEFAULT_TEXTNOTE_COLOR)

class ResizableTextItem(QGraphicsTextItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_resizing = False; self._resize_handle_active = None; self._resize_handle_size = 8.0
        self._original_mouse_pos_scene = QPointF(); self._original_rect_scene = QRectF()
        self._min_node_width = 100.0; self._min_node_height = FONT_SIZE + 16
        self.current_font_size = FONT_SIZE; self._min_font_size = 8; self._user_has_resized = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges); self.setAcceptHoverEvents(True)
        opt = QTextOption(self.document().defaultTextOption()); opt.setWrapMode(QTextOption.WrapMode.NoWrap); self.document().setDefaultTextOption(opt); self.setTextWidth(-1)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged: self.update()
        return super().itemChange(change, value)

    def _update_wrap_mode_based_on_state(self):
        opt = QTextOption(self.document().defaultTextOption())
        if self._user_has_resized and self.textWidth() > 0: opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        else: opt.setWrapMode(QTextOption.WrapMode.NoWrap); self.setTextWidth(-1)
        self.document().setDefaultTextOption(opt)

    def adjustFontSizeToFitRect(self, target_rect: QRectF | None = None):
        if target_rect is None: target_rect = self.boundingRect()
        doc_margin = self.document().documentMargin(); available_width = target_rect.width() - 2 * doc_margin; available_height = target_rect.height() - 2 * doc_margin
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
        super().paint(painter, option, widget)
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
            # Use event.position() which is correct for QGraphicsSceneMouseEvent
            pos_in_item = event.position().toPoint()
            for handle_name, rect in self.get_resize_handles_rects().items():
                if rect.contains(pos_in_item):
                    self._is_resizing = True; self._resize_handle_active = handle_name; self._original_mouse_pos_scene = event.scenePos(); self._original_rect_scene = self.sceneBoundingRect(); event.accept(); return
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
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing:
            self._is_resizing = False; self._resize_handle_active = None; self._user_has_resized = True
            self._update_wrap_mode_based_on_state(); self.adjustFontSizeToFitRect(self.boundingRect()); self.document().adjustSize(); self.prepareGeometryChange(); self.unsetCursor(); event.accept(); return
        super().mouseReleaseEvent(event)

class CalculationNode(ResizableTextItem):
    def __init__(self, scene, calculator):
        super().__init__()
        self.scene = scene
        self.calculator = calculator
        self.expression_str = ""
        self.defined_variable = None
        self.dependencies = set()
        self.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.setDefaultTextColor(COLOR_TEXT_INPUT)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction | Qt.TextInteractionFlag.TextSelectableByMouse)
        self.document().setDocumentMargin(8)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            cursor = self.textCursor()
            cursor.deletePreviousChar()
            self.setTextCursor(cursor)
            self.clearFocus()
        else:
            self.clear_result()

    def focusInEvent(self, event):
        self.clear_result()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        if self.scene and not self.toPlainText().strip():
            self.scene.removeItem(self)
            return
        self.update_node_and_propagate()

    def clear_result(self):
        current_text = self.toPlainText()
        if '→' in current_text:
            expression_only = current_text.partition('→')[0].strip()
            cursor_pos = self.textCursor().position()
            self.setPlainText(expression_only)
            cursor = self.textCursor()
            cursor.setPosition(min(cursor_pos, len(expression_only)))
            self.setTextCursor(cursor)
        self.expression_str = self.toPlainText()

    def update_node_and_propagate(self):
        self.expression_str = self.toPlainText().strip()
        if self.scene:
            self.scene.update_and_propagate(self)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        super().paint(painter, option, widget)

    def contextMenuEvent(self, event):
        menu = QMenu()
        action_cut = menu.addAction("Cut"); action_cut.triggered.connect(self.cut)
        action_copy = menu.addAction("Copy"); action_copy.triggered.connect(self.copy)
        action_paste = menu.addAction("Paste"); action_paste.triggered.connect(self.paste)
        menu.exec(event.screenPos())

    def set_display(self, result_str: str, is_error: bool, is_command_output: bool = False):
        if self.hasFocus():
            return
        safe_expression_html = self.expression_str.replace('<', '<').replace('>', '>').replace('\n', '<br>')
        safe_result_str_html = result_str.replace('<', '<').replace('>', '>').replace('\n', '<br>')
        if result_str:
            color = COLOR_TEXT_ERROR if is_error else COLOR_TEXT_RESULT
            html_content = f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression_html}</span> <span style='color: {color.name()};'>→ {safe_result_str_html}</span>"
        else:
            html_content = f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression_html}</span>"
        self.setHtml(html_content)
        self.document().adjustSize()
        self.prepareGeometryChange()
        self.adjustFontSizeToFitRect()

class LineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        pen = QPen(DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH); pen.setCapStyle(Qt.PenCapStyle.RoundCap); self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

class TextNoteItem(ResizableTextItem):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setPlainText(text); self.setFont(QFont(FONT_FAMILY, FONT_SIZE - 1)); self.setDefaultTextColor(DEFAULT_TEXTNOTE_COLOR)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction | Qt.TextInteractionFlag.TextSelectableByMouse); self.document().setDocumentMargin(6)
        self._min_node_height = (FONT_SIZE - 1) + 16; self.current_font_size = FONT_SIZE - 1

    def paint(self, painter: QPainter, option, widget=None):
        current_text = self.toPlainText()
        if not current_text.strip() and self.hasFocus():
            painter.setBrush(QColor(COLOR_NODE_BACKGROUND).lighter(105)); painter.setPen(QPen(COLOR_TEXT_RESULT, 0.5, Qt.PenStyle.DotLine)); painter.drawRoundedRect(self.boundingRect().adjusted(-2, -2, 2, 2), 3, 3)
        elif current_text.strip():
            painter.setBrush(QBrush(COLOR_NODE_BACKGROUND)); painter.setPen(Qt.PenStyle.NoPen); painter.drawRoundedRect(self.boundingRect(), 3, 3)
        super().paint(painter, option, widget)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.scene() and not self.toPlainText().strip() and not self._is_resizing: self.scene().removeItem(self); return
        self._update_text_item_state_after_change(is_focus_out=True)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event); self._update_text_item_state_after_change()

    def _update_text_item_state_after_change(self, is_focus_out=False):
        if is_focus_out: self._update_wrap_mode_based_on_state()
        self.document().adjustSize(); self.prepareGeometryChange(); self.adjustFontSizeToFitRect()

class PenStrokeItem(QGraphicsPathItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        pen = QPen(DEFAULT_PEN_COLOR, DEFAULT_PEN_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin); self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)       self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
