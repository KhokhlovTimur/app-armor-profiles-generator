import os
from typing import List

from PyQt5.QtWidgets import (
    QVBoxLayout, QTextEdit, QFormLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QMessageBox
)

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage
from src.ui.util.path_completer import ExecutablePathCompleter


class ProfileInfoPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.path = ""
        self.flags = ""

        self.setTitle("Selecting a target application.")
        layout = QFormLayout()

        label = QLabel("Select an executable file or application:")
        layout.addRow(label)

        path_layout = QHBoxLayout()
        self.app_path_line_edit = QLineEdit()
        completer = ExecutablePathCompleter(self.app_path_line_edit, False)
        self.app_path_line_edit.setCompleter(completer)
        self.app_path_line_edit.textEdited.connect(completer.update_model)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(lambda: self.browse_file(self))
        path_layout.addWidget(self.app_path_line_edit)

        path_layout.addWidget(browse_button)

        layout.addRow("Path:", path_layout)

        self.profile_flags_line_edit = QLineEdit()
        self.profile_flags_line_edit.setPlaceholderText("Example: enforced, attach_disconnected, mediate_deleted")
        layout.addRow("Flags:", self.profile_flags_line_edit)

        self.setLayout(layout)

    def validatePage(self):
        path = self.app_path_line_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Path not specified", "Please specify the path to the executable file.")
            return False
        return True

    def browse_file(self, parent):
        file_name, _ = QFileDialog.getOpenFileName(parent, "Select app", os.path.expanduser("~"))
        if file_name:
            self.app_path_line_edit.setText(file_name)

    def cleanupPage(self):
        super().cleanupPage()
        self.path = self.app_path_line_edit.text()
        self.flags = self.profile_flags_line_edit.text()
        print("Флаги профиля:", self.profile_flags_line_edit.text())

    def get_profile_fragment(self) -> str:
        profile_name = self.app_path_line_edit.text().strip()
        flags = self.profile_flags_line_edit.text() if f"flags=({self.profile_flags_line_edit.text()}) " else ""
        return f"profile {profile_name} {flags}{{\n"