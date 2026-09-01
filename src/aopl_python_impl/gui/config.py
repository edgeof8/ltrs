# config.py
import re
from enum import Enum
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# Window and Application Settings
WINDOW_TITLE = "Cosmic Scratchpad v0.2"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Font Settings
FONT_FAMILY = "Courier New"
FONT_SIZE = 14

# Color Scheme
COLOR_BACKGROUND = QColor("#1e1e2e")
COLOR_TEXT_INPUT = QColor("#cdd6f4")
COLOR_NODE_BACKGROUND = QColor("#313244")
COLOR_TEXT_RESULT = QColor("#89b4fa")
COLOR_TEXT_FINGERPRINT = QColor("#89dceb")
COLOR_TEXT_ERROR = QColor("#f38ba8")
DEFAULT_PEN_COLOR = QColor("#f9e2af")
DEFAULT_PEN_WIDTH = 1.5
DEFAULT_LINE_COLOR = QColor(Qt.GlobalColor.green)
DEFAULT_LINE_WIDTH = 2
DEFAULT_TEXTNOTE_COLOR = QColor("#bac2de")
COLOR_VAR_EDGE = QColor("#89b4fa")


# Regular Expressions
VARIABLE_REGEX = re.compile(r"\$([a-zA-Z_]\w*)")

# Drawing Tool Modes
class DrawingToolMode(Enum):
    CALCULATE = 0
    LINE = 1
    TEXT_NOTE = 2
    PEN = 3
