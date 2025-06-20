# gui_items.py
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsLineItem, QGraphicsPathItem, QApplication, QMenu, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent
from PySide6.QtGui import QColor, QBrush, QFont, QPen, QPainterPath, QPainter, QTextOption, QKeyEvent
from PySide6.QtCore import Qt, QRectF
from config import (FONT_FAMILY, FONT_SIZE, COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT,
                    COLOR_TEXT_RESULT, COLOR_TEXT_ERROR, DEFAULT_PEN_COLOR,
                    DEFAULT_PEN_WIDTH, DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH,
                    DEFAULT_TEXTNOTE_COLOR)

class CalculationNode(QGraphicsTextItem):
    """The main, editable calculation node."""
    def __init__(self, scene, calculator):
        super().__init__()
        self.scene = scene
        self.calculator = calculator
        self.expression_str = ""
        self.defined_variable = None
        self.dependencies = set()
        self._is_resizing = False
        self._resize_handle_active = None
        self._resize_handle_size = 8.0 # Use float for QRectF calculations

        self.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.setDefaultTextColor(COLOR_TEXT_INPUT)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        from PySide6.QtWidgets import QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True) # For resize cursors

        # --- Control Text Wrapping ---
        # Start with NoWrap, allow horizontal expansion. Wrapping controlled by setTextWidth later if resized.
        opt = QTextOption(self.document().defaultTextOption())
        opt.setWrapMode(QTextOption.WrapMode.NoWrap)
        self.document().setDefaultTextOption(opt)
        self.setTextWidth(-1) # No fixed width initially, allows horizontal expansion

        self.setPlainText("")
        self.document().setDocumentMargin(8)
        # self.update_node() # Don't update empty node on creation

    def keyPressEvent(self, event):
        # Shift+Enter for newline, Enter alone to finalize/unfocus
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                cursor = self.textCursor()
                cursor.insertText("\n")
                # self.update_node() will be called below
            else:
                self.clearFocus() # This will trigger focusOutEvent which calls update_node
                return

        super().keyPressEvent(event) # Handle all other key presses (typing characters, backspace, etc.)
        if event.text() or event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete) or \
           (event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.update_node()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        if not self.toPlainText().strip():
            self.scene.removeItem(self)
            return
        self.update_node()
        # After focus out, if it was being resized, ensure wrapping is set based on current width
        if self.textWidth() > 0: # If a text width has been set (e.g. by resizing)
            opt = QTextOption(self.document().defaultTextOption())
            opt.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere) # Or WordWrap
            self.document().setDefaultTextOption(opt)
        else: # No fixed width, so no wrap
            opt = QTextOption(self.document().defaultTextOption())
            opt.setWrapMode(QTextOption.WrapMode.NoWrap)
            self.document().setDefaultTextOption(opt)
        self.document().adjustSize()
        self.prepareGeometryChange()

    def paint(self, painter, option, widget=None):
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QWidget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        super().paint(painter, option, widget if widget else QWidget())

        if self.isSelected(): # Draw resize handles when selected
            painter.setBrush(QBrush(COLOR_TEXT_RESULT))
            painter.setPen(Qt.PenStyle.NoPen)
            for handle_rect in self.get_resize_handles_rects().values():
                painter.drawRect(handle_rect)

    def contextMenuEvent(self, event):
        menu = QMenu()
        action_cut = menu.addAction("Cut")
        action_copy = menu.addAction("Copy")
        action_paste = menu.addAction("Paste")

        def cut():
            cursor = self.textCursor()
            if cursor.hasSelection():
                QApplication.clipboard().setText(cursor.selectedText())
                cursor.removeSelectedText()
                self.setTextCursor(cursor)

        def copy():
            cursor = self.textCursor()
            if cursor.hasSelection():
                QApplication.clipboard().setText(cursor.selectedText())

        def paste():
            text = QApplication.clipboard().text()
            if text:
                cursor = self.textCursor()
                cursor.insertText(text)
                self.setTextCursor(cursor)

        action_cut.triggered.connect(cut)
        action_copy.triggered.connect(copy)
        action_paste.triggered.connect(paste)
        menu.exec(event.screenPos())

    def update_node(self):
        self.scene.update_and_propagate(self)

    def set_display(self, result_str, is_error):
        # Main logic for displaying text and managing the suffix node.
        safe_expression = self.expression_str.replace('<', '<').replace('>', '>')

        if result_str:
            color = COLOR_TEXT_ERROR if is_error else COLOR_TEXT_RESULT
            html_content = (f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression}</span> "
                           f"<span style='color: {color.name()};'>→ {result_str}</span>")
        else:
            html_content = f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression}</span>"

        cursor = self.textCursor()
        cursor_pos = cursor.position()
        self.setHtml(html_content)
        # Only restore cursor position if it's valid in the new content
        if cursor_pos < self.document().characterCount():
            cursor.setPosition(cursor_pos)
        self.setTextCursor(cursor)
        self.document().adjustSize()

    # --- Resizing Logic ---
    def get_resize_handles_rects(self) -> dict[str, QRectF]:
        # Returns a dictionary of QRectF for each handle, in item's local coordinates
        rect = self.boundingRect()
        s = self._resize_handle_size
        handles = {
            "bottom_right": QRectF(rect.right() - s, rect.bottom() - s, s, s),
            "top_left": QRectF(rect.left(), rect.top(), s, s),
            "top_right": QRectF(rect.right() - s, rect.top(), s, s),
            "bottom_left": QRectF(rect.left(), rect.bottom() - s, s, s),
        }
        return handles

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent): # Import QGraphicsSceneHoverEvent
        if self.isSelected(): # Only show resize cursors if selected
            self.setFocus() # Keep focus when hovering over selected item for resizing
            current_pos_in_item = event.pos()
            handles = self.get_resize_handles_rects()
            if handles["bottom_right"].contains(current_pos_in_item) or \
               handles["top_left"].contains(current_pos_in_item):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif handles["top_right"].contains(current_pos_in_item) or \
                 handles["bottom_left"].contains(current_pos_in_item):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.IBeamCursor) # Default for text item
            return # Event handled for cursor
        self.setCursor(Qt.CursorShape.IBeamCursor) # Default if not selected
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent): # Import QGraphicsSceneMouseEvent
        if self.isSelected() and event.button() == Qt.MouseButton.LeftButton:
            current_pos_in_item = event.pos()
            for handle_name, rect in self.get_resize_handles_rects().items():
                if rect.contains(current_pos_in_item):
                    self._is_resizing = True
                    self._resize_handle_active = handle_name
                    self._original_mouse_pos_scene = self.mapToScene(current_pos_in_item) # event.scenePos()
                    self._original_rect_scene = self.sceneBoundingRect() # Use sceneBoundingRect for scene delta
                    self._original_item_pos = self.pos()
                    self.prepareGeometryChange()
                    event.accept()
                    return

        self._is_resizing = False
        super().mousePressEvent(event) # For text selection and standard item moving

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing and self._resize_handle_active:
            new_mouse_pos_scene = event.scenePos()
            delta_scene = new_mouse_pos_scene - self._original_mouse_pos_scene

            # For QGraphicsTextItem, we primarily control width via setTextWidth
            # Height is mostly content-driven after wrapping.
            current_width = self._original_rect_scene.width()

            if self._resize_handle_active == "bottom_right" or self._resize_handle_active == "top_right":
                new_width = current_width + delta_scene.x()
            elif self._resize_handle_active == "bottom_left" or self._resize_handle_active == "top_left":
                new_width = current_width - delta_scene.x()
            else: # Should not happen if handle is active
                super().mouseMoveEvent(event)
                return

            min_width = self._resize_handle_size * 4 # Ensure some minimum width
            if new_width < min_width: new_width = min_width

            self.prepareGeometryChange()
            self.setTextWidth(new_width) # This enables wrapping
            opt = QTextOption(self.document().defaultTextOption())
            opt.setWrapMode(QTextOption.WrapMode.WordWrap) # Or WrapAtWordBoundaryOrAnywhere
            self.document().setDefaultTextOption(opt)
            self.document().adjustSize() # Recalculate height based on new width and wrapped text
            self.update()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_handle_active = None
            # Final adjustment and update
            self.document().adjustSize()
            self.prepareGeometryChange()
            if isinstance(self, CalculationNode): # If it's a calc node, re-evaluate
                 self.update_node()
            self.setCursor(Qt.CursorShape.IBeamCursor) # Reset cursor
            event.accept()
            return
        super().mouseReleaseEvent(event)

class LineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        pen = QPen(DEFAULT_LINE_COLOR, DEFAULT_LINE_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        from PySide6.QtWidgets import QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

class TextNoteItem(QGraphicsTextItem):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setPlainText(text)
        self.setFont(QFont(FONT_FAMILY, FONT_SIZE - 1))
        self.setDefaultTextColor(DEFAULT_TEXTNOTE_COLOR)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        from PySide6.QtWidgets import QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.document().setDocumentMargin(6)

    def paint(self, painter: QPainter, option, widget=None):
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QWidget

        # Draw a background, especially a visual cue if empty and focused
        current_text = self.toPlainText()
        if not current_text.strip() and self.hasFocus():
            # Empty and focused: draw a subtle editing box
            painter.setBrush(QColor(COLOR_NODE_BACKGROUND).lighter(105))
            painter.setPen(QPen(COLOR_TEXT_RESULT, 0.5, Qt.PenStyle.DotLine))
            painter.drawRoundedRect(self.boundingRect().adjusted(-2, -2, 2, 2), 3, 3)
        elif current_text.strip():
            painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.boundingRect(), 3, 3)

        super().paint(painter, option, widget if widget else QWidget())

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        if not self.toPlainText().strip():
            if self.scene():
                self.scene().removeItem(self)

class PenStrokeItem(QGraphicsPathItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        pen = QPen(DEFAULT_PEN_COLOR, DEFAULT_PEN_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)
        from PySide6.QtWidgets import QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
