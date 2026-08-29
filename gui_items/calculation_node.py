from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QColor, QBrush, QKeyEvent, QPainter
from PySide6.QtCore import Qt
from config import (FONT_FAMILY, FONT_SIZE, COLOR_NODE_BACKGROUND, COLOR_TEXT_INPUT,
                    COLOR_TEXT_RESULT, COLOR_TEXT_ERROR)
from gui_items.base_item import ResizableTextItem

if TYPE_CHECKING:
    from cosmic_scene import CosmicScene

class CalculationNode(ResizableTextItem):
    def __init__(self, scene, calculator):
        super().__init__()
        self.calculator = calculator
        self.expression_str = ""
        self.defined_variable: str | None = None
        self.dependencies = set()
        self.setFont(QFont(FONT_FAMILY, FONT_SIZE))
        self.setDefaultTextColor(COLOR_TEXT_INPUT)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction | Qt.TextInteractionFlag.TextSelectableByMouse)
        self.document().setDocumentMargin(8)

    def scene(self) -> 'CosmicScene':
        return super().scene()  # type: ignore

    def cut(self):
        self.copy()
        scene = self.scene()
        if scene and hasattr(scene, 'removeItem'):
            scene.removeItem(self)  # type: ignore

    def copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.toPlainText())

    def paste(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.setPlainText(text)
            self.update_node_and_propagate()

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
        scene = self.scene()
        if scene and hasattr(scene, 'removeItem') and not self.toPlainText().strip():
            scene.removeItem(self)  # type: ignore
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
        scene = self.scene()
        if scene and hasattr(scene, 'update_and_propagate'):
            scene.update_and_propagate(self)  # type: ignore

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        super().paint(painter, option, widget)

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
