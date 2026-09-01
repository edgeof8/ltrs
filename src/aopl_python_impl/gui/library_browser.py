from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QListWidgetItem
from PySide6.QtCore import Qt
import requests
import json

class LibraryBrowserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cosmic Library Browser")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)

        # List of scratchpads
        self.scratchpad_list = QListWidget()
        self.scratchpad_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.scratchpad_list)

        # Buttons
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.open_button = QPushButton("Download & Open")
        self.cancel_button = QPushButton("Cancel")

        self.refresh_button.clicked.connect(self.refresh_list)
        self.open_button.clicked.connect(self.download_and_open)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Initial load of scratchpads
        self.refresh_list()

    def refresh_list(self):
        """Fetch the list of scratchpads from the server and update the UI."""
        self.scratchpad_list.clear()
        try:
            response = requests.get('http://localhost:8000/list')
            if response.status_code == 200:
                scratchpads = response.json()
                for scratchpad in scratchpads:
                    item = QListWidgetItem(f"{scratchpad['title']} by {scratchpad['author']}")
                    item.setData(Qt.UserRole, scratchpad['uuid'])
                    item.setToolTip(scratchpad.get('description', ''))
                    self.scratchpad_list.addItem(item)
            else:
                self.parent().status_bar.showMessage(f"Error fetching library list: {response.text}", 5000)
        except Exception as e:
            self.parent().status_bar.showMessage(f"Error fetching library list: {str(e)}", 5000)

    def download_and_open(self):
        """Download the selected scratchpad and load it into the application."""
        selected_item = self.scratchpad_list.currentItem()
        if not selected_item:
            self.parent().status_bar.showMessage("Please select a scratchpad to open.", 5000)
            return

        uuid = selected_item.data(Qt.UserRole)
        try:
            response = requests.get(f'http://localhost:8000/scratchpad/{uuid}')
            if response.status_code == 200:
                data = response.json()
                self.parent().load_scene_from_data(data)
                self.parent().status_bar.showMessage(f"Loaded scratchpad '{selected_item.text().split(' by ')[0]}'", 5000)
                self.accept()
            else:
                self.parent().status_bar.showMessage(f"Error downloading scratchpad: {response.text}", 5000)
        except Exception as e:
            self.parent().status_bar.showMessage(f"Error downloading scratchpad: {str(e)}", 5000)
