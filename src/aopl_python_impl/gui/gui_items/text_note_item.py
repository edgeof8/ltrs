from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QColor, QBrush, QPen, QPainter, QKeyEvent
from PySide6.QtCore import Qt
from ..config import (FONT_FAMILY, FONT_SIZE, COLOR_NODE_BACKGROUND, COLOR_TEXT_RESULT,
                    DEFAULT_TEXTNOTE_COLOR)
from .base_item import ResizableTextItem

if TYPE_CHECKING:
    from ..cosmic_scene import CosmicScene

class TextNoteItem(ResizableTextItem):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setPlainText(text); self.setFont(QFont(FONT_FAMILY, FONT_SIZE - 1)); self.setDefaultTextColor(DEFAULT_TEXTNOTE_COLOR)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction | Qt.TextInteractionFlag.TextSelectableByMouse); self.document().setDocumentMargin(6)
        self._min_node_height = (FONT_SIZE - 1) + 16; self.current_font_size = FONT_SIZE - 1

    def scene(self) -> 'CosmicScene':
        return super().scene()  # type: ignore

    def cut(self):
        self.copy()
        if self.scene():
            self.scene().removeItem(self)

    def copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.toPlainText())

    def paste(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.setPlainText(text)

    def paint(self, painter: QPainter, option, widget=None):
        current_text = self.toPlainText()
        if not current_text.strip() and self.hasFocus():
            painter.setBrush(QColor(COLOR_NODE_BACKGROUND).lighter(105)); painter.setPen(QPen(COLOR_TEXT_RESULT, 0.5, Qt.PenStyle.DotLine)); painter.drawRoundedRect(self.boundingRect().adjusted(-2, -2, 2, 2), 3, 3)
        elif current_text.strip():
            painter.setBrush(QBrush(COLOR_NODE_BACKGROUND)); painter.setPen(Qt.PenStyle.NoPen); painter.drawRoundedRect(self.boundingRect(), 3, 3)
        super().paint(painter, option, widget)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.scene() and hasattr(self.scene(), 'removeItem') and not self.toPlainText().strip() and not self._is_resizing: self.scene().removeItem(self); return  # type: ignore
        self._update_text_item_state_after_change(is_focus_out=True)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event); self._update_text_item_state_after_change()

    def _update_text_item_state_after_change(self, is_focus_out=False):
        if is_focus_out: self._update_wrap_mode_based_on_state()
        self.document().adjustSize(); self.prepareGeometryChange(); self.adjustFontSizeToFitRect()
