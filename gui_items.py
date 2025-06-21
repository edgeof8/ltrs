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
        self._resize_handle_active = None # e.g., "bottom_right"
        self._resize_handle_size = 8.0 # Size of resize handles (float)
        self._original_mouse_pos_scene = QPointF()
        self._original_rect_scene = QRectF()
        self._original_item_rect_local = QRectF()
        self._original_item_pos = QPointF()
        self._min_node_width = 100.0 # Minimum width for a node
        self._min_node_height = FONT_SIZE + 16 # Min height based on font + padding
        self._original_item_width = 0.0 # Store original width for proportional resize if needed
        self._original_item_height = 0.0 # Store original height for proportional resize if needed
        self.current_font_size = FONT_SIZE # Store current font size for the node
        self._min_font_size = 8 # Minimum font size for auto-adjust
        self._user_has_resized = False # Flag to track if user has manually resized

        self.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.setDefaultTextColor(COLOR_TEXT_INPUT)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        from PySide6.QtWidgets import QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True) # Crucial for hoverMoveEvent to work

        # Text Wrapping Control
        # Start with NoWrap, allow horizontal expansion. Wrapping controlled by setTextWidth later if resized.
        opt = QTextOption(self.document().defaultTextOption())
        opt.setWrapMode(QTextOption.WrapMode.NoWrap)
        self.document().setDefaultTextOption(opt)
        self.setTextWidth(-1) # No fixed width initially, allows horizontal expansion

        self.setPlainText("")
        self.document().setDocumentMargin(8)
        # self.update_node() # Don't update empty node on creation

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # When selection changes, update to show/hide handles (paint method handles drawing)
            self.update()
        return super().itemChange(change, value)

    def _update_wrap_mode_based_on_state(self):
        """Helper to set wrap mode based on whether user has resized."""
        opt = QTextOption(self.document().defaultTextOption())
        if self._user_has_resized and self.textWidth() > 0:
            opt.setWrapMode(QTextOption.WrapMode.WordWrap) # Wrap if user set a width
        else:
            opt.setWrapMode(QTextOption.WrapMode.NoWrap) # Expand if no user width
        self.document().setDefaultTextOption(opt)

    def adjustFontSizeToFitRect(self, target_rect: QRectF | None = None):
        if target_rect is None:
            target_rect = self.boundingRect() # Current bounding rect of the item

        # Available width/height for text, considering margins
        doc_margin = self.document().documentMargin()
        available_width = target_rect.width() - 2 * doc_margin
        available_height = target_rect.height() - 2 * doc_margin

        if available_width <= 0 or available_height <= 0:
            return # Not enough space

        current_text = self.toPlainText()
        if not current_text:
            self.setFont(QFont(FONT_FAMILY, FONT_SIZE)) # Reset to default if empty
            return

        # Iterative approach to find best font size
        font_size = self.current_font_size # Start with current or default max
        font = QFont(FONT_FAMILY)

        while font_size >= self._min_font_size:
            font.setPixelSize(font_size) # Use pixel size for more granular control
            # Or use font.setPointSize(font_size) if FONT_SIZE is in points
            metrics = QFontMetrics(font)
            # Get bounding rect for the text with current font size and available width for wrapping
            # The document's textWidth should be set to available_width for this to be accurate
            self.document().setTextWidth(available_width) # Let document know how wide it can be
            text_rect = metrics.boundingRect(0, 0, int(available_width), 10000, # Use available_width for wrap calc
                                             Qt.TextFlag.TextWordWrap, current_text)

            if text_rect.height() <= available_height and text_rect.width() <= available_width:
                break # This font size fits
            font_size -= 1 # Decrease font size and try again

        if font_size < self._min_font_size: font_size = self._min_font_size # Clamp to min

        final_font = QFont(FONT_FAMILY)
        final_font.setPixelSize(font_size)
        self.setFont(final_font)
        self.current_font_size = font_size

        # After font change, ensure document uses the target width for wrapping
        self.document().setTextWidth(available_width)
        self.document().adjustSize() # Adjust document to new font/wrapping
        self.prepareGeometryChange() # Inform that geometry will change
        self.update() # Repaint

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier): # Shift+Enter
                cursor = self.textCursor()
                cursor.insertBlock() # Inserts a new paragraph (newline)
                # Do NOT accept or return yet. Let super() also see it if it needs to.
                # The update will happen after super().
            else: # Enter ALONE - finalize and unfocus
                self.clearFocus() # Triggers focusOutEvent, which handles updates
                event.accept() # We handle this, super() shouldn't.
                return

        # For Shift+Enter (if not returned) and all other keys:
        super().keyPressEvent(event) # CRITICAL: Let base class process the key for text input/manipulation

        # Now, after super() has acted (or we inserted a block for Shift+Enter), update our state.
        self._update_text_item_state_after_change() # This calls adjustFont, update_node

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.document().adjustSize()
        # When focus is lost, clear any text selection
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        if not self.toPlainText().strip():
            self.scene.removeItem(self)
            return

        self._update_text_item_state_after_change(is_focus_out=True)

    def _update_text_item_state_after_change(self, is_focus_out=False):
        """Centralized method to update geometry, font, and trigger AoP calc."""
        if is_focus_out: # On focus out, ensure wrap mode is correctly set first
            self._update_wrap_mode_based_on_state()

        # This order is important: set wrap, then adjust size, then prepare geometry, then font, then evaluate
        self._update_wrap_mode_based_on_state() # Ensure correct wrap before adjusting font
        self.document().adjustSize() # Adjust document size first based on content and wrap mode
        self.prepareGeometryChange() # Then prepare for geometry change
        self.adjustFontSizeToFitRect() # Then adjust font
        self.update_node()             # Then evaluate

    def paint(self, painter, option, widget=None):
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QWidget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        super().paint(painter, option, widget if widget else QWidget()) # Let base class paint text

        if self.isSelected(): # Draw resize handles when selected
            painter.setBrush(QBrush(QColor(COLOR_TEXT_RESULT).lighter(110))) # Slightly lighter handles
            painter.setPen(Qt.PenStyle.NoPen)
            for handle_rect in self.get_resize_handles_rects().values():
                painter.drawEllipse(handle_rect) # Use ellipse for rounder handles

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
        if self.scene: self.scene.update_and_propagate(self)

    def set_display(self, result_str: str, is_error: bool, is_command_output: bool = False): # Added type hints and default
        safe_expression_html = self.expression_str.replace('<', '<').replace('>', '>').replace('\n', '<br>')
        safe_result_str_html = result_str.replace('<', '<').replace('>', '>').replace('\n', '<br>')

        # --- Handle wrapping for command output ---
        # This logic should be primarily in focusOutEvent or after resize
        doc_opt = QTextOption(self.document().defaultTextOption())
        original_text_width = self.textWidth() # Store current text width

        if is_command_output:
            # For command output that is expected to be multi-line and wrap,
            # set a text width temporarily if not already constrained by user resize.
            doc_opt.setWrapMode(QTextOption.WrapMode.WordWrap) # Enable wrapping
            if original_text_width < 0: # If width is auto (-1), set a reasonable default for commands
                self.setTextWidth(450) # Default width for command output, adjust as needed
        else:
            # For calculation results, respect NoWrap if not resized, or WordWrap if resized
            if original_text_width < 0: # Not user-resized
                doc_opt.setWrapMode(QTextOption.WrapMode.NoWrap)
            else: # User has resized it
                doc_opt.setWrapMode(QTextOption.WrapMode.WordWrap)
            self.document().setDefaultTextOption(doc_opt)

        if result_str:
            color = COLOR_TEXT_ERROR if is_error else COLOR_TEXT_RESULT
            html_content = (f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression_html}</span> "
                           f"<span style='color: {color.name()};'>→ {safe_result_str_html}</span>")
        else:
            html_content = f"<span style='color: {COLOR_TEXT_INPUT.name()};'>{safe_expression_html}</span>"

        cursor = self.textCursor()
        cursor_pos = cursor.position()
        self.setHtml(html_content)
        # Only restore cursor position if it's valid in the new content
        if cursor_pos < self.document().characterCount():
            cursor.setPosition(cursor_pos)
        self.setTextCursor(cursor)
        self.document().adjustSize()
        self.prepareGeometryChange()

        # If we temporarily set a width for command output and it wasn't user-resized before,
        # revert textWidth. The wrap mode will be reset by focusOutEvent if needed.
        if is_command_output and original_text_width < 0 and self.textWidth() != original_text_width:
            # Check if it still contains the command output; if user edited, might not revert.
            # This revert is tricky. Simpler: command output nodes might just stay at that width.
            # Or, only set textWidth if it's truly a multi-line help text.
            if result_str.count("\n") > 3: # Heuristic for multi-line help-like output
                pass # Keep the command output width
            else:
                self.setTextWidth(-1) # Revert to auto-expanding width after display
            # self.document().setDefaultTextOption(doc_opt) # Wrap mode handled by focusOut/resize

    # --- Resizing Logic ---
    def get_resize_handles_rects(self) -> dict[str, QRectF]:
        # Returns a dictionary of QRectF for each handle, in item's local coordinates
        rect = self.boundingRect()
        s = self._resize_handle_size
        handles = {
            "top_left": QRectF(rect.left(), rect.top(), s, s),
            "top_right": QRectF(rect.right() - s, rect.top(), s, s),
            "bottom_left": QRectF(rect.left(), rect.bottom() - s, s, s),
            "bottom_right": QRectF(rect.right() - s, rect.bottom() - s, s, s),
        }
        # For side handles (optional, add if you want 8-way resizing)
        # handles["middle_left"] = QRectF(rect.left(), rect.center().y() - s / 2, s, s)
        # handles["middle_right"] = QRectF(rect.right() - s, rect.center().y() - s / 2, s, s)
        # handles["top_middle"] = QRectF(rect.center().x() - s / 2, rect.top(), s, s)
        # handles["bottom_middle"] = QRectF(rect.center().x() - s / 2, rect.bottom() - s, s, s)
        return handles

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent): # Import QGraphicsSceneHoverEvent
        if self.isSelected() and not self._is_resizing:
            pos_in_item = event.pos()
            handles = self.get_resize_handles_rects()
            if handles["top_left"].contains(pos_in_item) or handles["bottom_right"].contains(pos_in_item):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif handles["top_right"].contains(pos_in_item) or \
                 handles["bottom_left"].contains(pos_in_item):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.IBeamCursor) # Default for text item when selected
            return # Event handled for cursor
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor) # Default if not selected or if resizing
        super().hoverMoveEvent(event)
        event.accept() # Accept hover event if we want to control cursor exclusively

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent): # Import QGraphicsSceneMouseEvent
        if self.isSelected() and event.button() == Qt.MouseButton.LeftButton:
            pos_in_item = event.pos()
            for handle_name, rect in self.get_resize_handles_rects().items(): # Check if click is on a handle
                if rect.contains(pos_in_item):
                    self._is_resizing = True
                    self._resize_handle_active = handle_name
                    self._original_mouse_pos_scene = event.scenePos()
                    # Store original geometry: local rect for size, scene rect for positioning
                    self._original_item_rect_local = self.boundingRect()
                    self._original_rect_scene = self.sceneBoundingRect()
                    self.prepareGeometryChange()
                    event.accept()
                    return

        self._is_resizing = False # Ensure reset if not clicking a handle
        super().mousePressEvent(event) # IMPORTANT: Let base class handle press for text cursor placement
                                       # and for initiating item movement if not on a handle.

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent): # QGraphicsSceneMouseEvent
        if self._is_resizing and self._resize_handle_active:
            current_mouse_pos_scene = event.scenePos()
            delta_scene = current_mouse_pos_scene - self._original_mouse_pos_scene

            # Calculate new proposed rectangle in scene coordinates
            new_scene_rect = QRectF(self._original_rect_scene) # Start with original scene bounding rect

            if self._resize_handle_active == "bottom_right":
                new_scene_rect.setRight(self._original_rect_scene.right() + delta_scene.x())
                new_scene_rect.setBottom(self._original_rect_scene.bottom() + delta_scene.y())
            elif self._resize_handle_active == "top_right":
                new_scene_rect.setTop(self._original_rect_scene.top() + delta_scene.y())
                new_scene_rect.setRight(self._original_rect_scene.right() + delta_scene.x())
            elif self._resize_handle_active == "bottom_left":
                new_scene_rect.setLeft(self._original_rect_scene.left() + delta_scene.x())
                new_scene_rect.setBottom(self._original_rect_scene.bottom() + delta_scene.y())
            elif self._resize_handle_active == "top_left":
                new_scene_rect.setLeft(self._original_rect_scene.left() + delta_scene.x())
                new_scene_rect.setTop(self._original_rect_scene.top() + delta_scene.y())

            # Ensure minimum size
            if new_scene_rect.width() < self._min_node_width:
                if self._resize_handle_active in ["top_left", "bottom_left"]:
                    new_scene_rect.setLeft(new_scene_rect.right() - self._min_node_width)
                else:
                    new_scene_rect.setWidth(self._min_node_width)
            if new_scene_rect.height() < self._min_node_height:
                if self._resize_handle_active in ["top_left", "top_right"]:
                    new_scene_rect.setTop(new_scene_rect.bottom() - self._min_node_height)
                else:
                    new_scene_rect.setHeight(self._min_node_height)

            self.prepareGeometryChange()
            # Set item's new position (top-left corner in scene coordinates)
            self.setPos(new_scene_rect.topLeft())
            # Set the textWidth for wrapping. Height will be determined by content.
            # The actual bounding rect will be updated after text layout.
            self.document().setTextWidth(new_scene_rect.width() - 2 * self.document().documentMargin())
            self._user_has_resized = True # Mark that user has resized
            self._update_wrap_mode_based_on_state() # Enable wrapping
            self.adjustFontSizeToFitRect(QRectF(0, 0, new_scene_rect.width(), new_scene_rect.height())) # Adjust font to new rect

            self.update()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent): # QGraphicsSceneMouseEvent
        if self._is_resizing:
            self._is_resizing = False
            self._resize_handle_active = None
            # Final font size adjustment based on the final rect
            self._user_has_resized = True # Confirm user has resized
            self._update_wrap_mode_based_on_state() # Set final wrap mode
            self.adjustFontSizeToFitRect(self.boundingRect()) # Use current actual bounding rect
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
        self._is_resizing = False
        self._resize_handle_active: str | None = None
        self._resize_handle_size = 8.0
        self._original_mouse_pos_scene = QPointF()
        self._original_rect_scene = QRectF()
        self._original_item_rect_local = QRectF()
        self._original_item_pos = QPointF()
        self._min_node_width = 100.0
        self._min_node_height = (FONT_SIZE - 1) + 16
        self.current_font_size = FONT_SIZE - 1
        self._min_font_size = 8
        self._user_has_resized = False
        self.setAcceptHoverEvents(True)

        # --- Control Text Wrapping ---
        opt = QTextOption(self.document().defaultTextOption())
        opt.setWrapMode(QTextOption.WrapMode.NoWrap)
        self.document().setDefaultTextOption(opt)
        self.setTextWidth(-1) # Start with auto-width

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

        if self.isSelected(): # Draw resize handles when selected
            painter.setBrush(QBrush(QColor(COLOR_TEXT_RESULT).lighter(110))) # Slightly lighter handles
            painter.setPen(Qt.PenStyle.NoPen)
            for handle_rect in self.get_resize_handles_rects().values():
                painter.drawEllipse(handle_rect) # Use ellipse for rounder handles

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.scene() and not self.toPlainText().strip() and not self._is_resizing:
            self.scene().removeItem(self)
            return
        self._update_text_item_state_after_change(is_focus_out=True)

    # Add keyPressEvent to TextNoteItem for Shift+Enter and font adjustment
    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event) # Let base class handle text input/newlines
        # After text may have changed, update state
        self._update_text_item_state_after_change()

    def _update_text_item_state_after_change(self, is_focus_out=False):
        if is_focus_out:
            self._update_wrap_mode_based_on_state()

        self.document().adjustSize()
        self.prepareGeometryChange()
        self.adjustFontSizeToFitRect()
        # No self.update_node() for TextNoteItem

    def _update_wrap_mode_based_on_state(self):
        """Helper to set wrap mode based on whether user has resized."""
        opt = QTextOption(self.document().defaultTextOption())
        if self._user_has_resized and self.textWidth() > 0:
            opt.setWrapMode(QTextOption.WrapMode.WordWrap) # Wrap if user set a width
        else:
            opt.setWrapMode(QTextOption.WrapMode.NoWrap) # Expand if no user width
            self.setTextWidth(-1) # Ensure it can expand if NoWrap
        self.document().setDefaultTextOption(opt)

    def adjustFontSizeToFitRect(self, target_rect: QRectF | None = None):
        if target_rect is None:
            target_rect = self.boundingRect() # Current bounding rect of the item

        # Available width/height for text, considering margins
        doc_margin = self.document().documentMargin()
        available_width = target_rect.width() - 2 * doc_margin
        available_height = target_rect.height() - 2 * doc_margin

        if available_width <= 0 or available_height <= 0:
            return # Not enough space

        current_text = self.toPlainText()
        if not current_text:
            self.setFont(QFont(FONT_FAMILY, self.current_font_size)) # Reset to default if empty
            return

        # Iterative approach to find best font size
        font_size = self.current_font_size # Start with current or default max
        font = QFont(FONT_FAMILY)

        while font_size >= self._min_font_size:
            font.setPixelSize(font_size) # Use pixel size for more granular control
            metrics = QFontMetrics(font)
            # Get bounding rect for the text with current font size and available width for wrapping
            self.document().setTextWidth(available_width) # Let document know how wide it can be
            text_rect = metrics.boundingRect(0, 0, int(available_width), 10000, # Use available_width for wrap calc
                                             Qt.TextFlag.TextWordWrap, current_text)

            if text_rect.height() <= available_height and text_rect.width() <= available_width:
                break # This font size fits
            font_size -= 1 # Decrease font size and try again

        if font_size < self._min_font_size: font_size = self._min_font_size # Clamp to min

        final_font = QFont(FONT_FAMILY)
        final_font.setPixelSize(font_size)
        self.setFont(final_font)
        self.current_font_size = font_size

        # After font change, ensure document uses the target width for wrapping
        self.document().setTextWidth(available_width)
        self.document().adjustSize() # Adjust document to new font/wrapping
        self.prepareGeometryChange() # Inform that geometry will change
        self.update() # Repaint

    def get_resize_handles_rects(self) -> dict[str, QRectF]:
        # Returns a dictionary of QRectF for each handle, in item's local coordinates
        rect = self.boundingRect()
        s = self._resize_handle_size
        handles = {
            "top_left": QRectF(rect.left(), rect.top(), s, s),
            "top_right": QRectF(rect.right() - s, rect.top(), s, s),
            "bottom_left": QRectF(rect.left(), rect.bottom() - s, s, s),
            "bottom_right": QRectF(rect.right() - s, rect.bottom() - s, s, s),
        }
        return handles

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.isSelected() and not self._is_resizing:
            pos_in_item = event.pos()
            handles = self.get_resize_handles_rects()
            if handles["top_left"].contains(pos_in_item) or handles["bottom_right"].contains(pos_in_item):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif handles["top_right"].contains(pos_in_item) or \
                 handles["bottom_left"].contains(pos_in_item):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.IBeamCursor) # Default for text item when selected
            return # Event handled for cursor
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor) # Default if not selected or if resizing
        super().hoverMoveEvent(event)
        event.accept() # Accept hover event if we want to control cursor exclusively

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.isSelected() and event.button() == Qt.MouseButton.LeftButton:
            pos_in_item = event.pos()
            for handle_name, rect in self.get_resize_handles_rects().items(): # Check if click is on a handle
                if rect.contains(pos_in_item):
                    self._is_resizing = True
                    self._resize_handle_active = handle_name
                    self._original_mouse_pos_scene = event.scenePos()
                    # Store original geometry: local rect for size, scene rect for positioning
                    self._original_item_rect_local = self.boundingRect()
                    self._original_rect_scene = self.sceneBoundingRect()
                    self.prepareGeometryChange()
                    event.accept()
                    return

        self._is_resizing = False # Ensure reset if not clicking a handle
        super().mousePressEvent(event) # IMPORTANT: Let base class handle press for text cursor placement

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing and self._resize_handle_active:
            current_mouse_pos_scene = event.scenePos()
            delta_scene = current_mouse_pos_scene - self._original_mouse_pos_scene

            # Calculate new proposed rectangle in scene coordinates
            new_scene_rect = QRectF(self._original_rect_scene) # Start with original scene bounding rect

            if self._resize_handle_active == "bottom_right":
                new_scene_rect.setRight(self._original_rect_scene.right() + delta_scene.x())
                new_scene_rect.setBottom(self._original_rect_scene.bottom() + delta_scene.y())
            elif self._resize_handle_active == "top_right":
                new_scene_rect.setTop(self._original_rect_scene.top() + delta_scene.y())
                new_scene_rect.setRight(self._original_rect_scene.right() + delta_scene.x())
            elif self._resize_handle_active == "bottom_left":
                new_scene_rect.setLeft(self._original_rect_scene.left() + delta_scene.x())
                new_scene_rect.setBottom(self._original_rect_scene.bottom() + delta_scene.y())
            elif self._resize_handle_active == "top_left":
                new_scene_rect.setLeft(self._original_rect_scene.left() + delta_scene.x())
                new_scene_rect.setTop(self._original_rect_scene.top() + delta_scene.y())

            # Ensure minimum size
            if new_scene_rect.width() < self._min_node_width:
                if self._resize_handle_active in ["top_left", "bottom_left"]:
                    new_scene_rect.setLeft(new_scene_rect.right() - self._min_node_width)
                else:
                    new_scene_rect.setWidth(self._min_node_width)
            if new_scene_rect.height() < self._min_node_height:
                if self._resize_handle_active in ["top_left", "top_right"]:
                    new_scene_rect.setTop(new_scene_rect.bottom() - self._min_node_height)
                else:
                    new_scene_rect.setHeight(self._min_node_height)

            self.prepareGeometryChange()
            # Set item's new position (top-left corner in scene coordinates)
            self.setPos(new_scene_rect.topLeft())
            # Set the textWidth for wrapping. Height will be determined by content.
            # The actual bounding rect will be updated after text layout.
            self.document().setTextWidth(new_scene_rect.width() - 2 * self.document().documentMargin())
            self._user_has_resized = True # Mark that user has resized
            self._update_wrap_mode_based_on_state() # Enable wrapping
            self.adjustFontSizeToFitRect(QRectF(0, 0, new_scene_rect.width(), new_scene_rect.height())) # Adjust font to new rect

            self.update()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_handle_active = None
            # Final font size adjustment based on the final rect
            self._user_has_resized = True # Confirm user has resized
            self._update_wrap_mode_based_on_state() # Set final wrap mode
            self.adjustFontSizeToFitRect(self.boundingRect()) # Use current actual bounding rect
            self.document().adjustSize()
            self.prepareGeometryChange()

            self.setCursor(Qt.CursorShape.IBeamCursor) # Reset cursor
            event.accept()
            return
        super().mouseReleaseEvent(event)

class PenStrokeItem(QGraphicsPathItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        pen = QPen(DEFAULT_PEN_COLOR, DEFAULT_PEN_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)
        from PySide6.QtWidgets import QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
