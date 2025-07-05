import tempfile
import json
import os
import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QFileDialog
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import Qt

# Assuming WINDOW_TITLE is needed for ShareDialog
from config import WINDOW_TITLE

class PlotConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Configuration")
        layout = QVBoxLayout(self)

        # Expression
        expr_layout = QHBoxLayout()
        expr_label = QLabel("Expression:")
        self.expr_input = QLineEdit()
        expr_layout.addWidget(expr_label)
        expr_layout.addWidget(self.expr_input)
        layout.addLayout(expr_layout)

        # Variable
        var_layout = QHBoxLayout()
        var_label = QLabel("Variable:")
        self.var_input = QLineEdit()
        var_layout.addWidget(var_label)
        var_layout.addWidget(self.var_input)
        layout.addLayout(var_layout)

        # Start Value
        start_layout = QHBoxLayout()
        start_label = QLabel("Start Value:")
        self.start_input = QLineEdit("1")
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_input)
        layout.addLayout(start_layout)

        # End Value
        end_layout = QHBoxLayout()
        end_label = QLabel("End Value:")
        self.end_input = QLineEdit("100")
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_input)
        layout.addLayout(end_layout)

        # Steps
        steps_layout = QHBoxLayout()
        steps_label = QLabel("Steps:")
        self.steps_input = QLineEdit("200")
        steps_layout.addWidget(steps_label)
        steps_layout.addWidget(self.steps_input)
        layout.addLayout(steps_layout)

        # Logarithmic options
        self.log_x_check = QCheckBox("Logarithmic X-axis")
        self.log_y_check = QCheckBox("Logarithmic Y-axis")
        layout.addWidget(self.log_x_check)
        layout.addWidget(self.log_y_check)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)


class ShareDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Share to Cosmic Library")
        layout = QVBoxLayout(self)

        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)

        # Author
        author_layout = QHBoxLayout()
        author_label = QLabel("Author:")
        self.author_input = QLineEdit()
        author_layout.addWidget(author_label)
        author_layout.addWidget(self.author_input)
        layout.addLayout(author_layout)

        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(100)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Share")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
