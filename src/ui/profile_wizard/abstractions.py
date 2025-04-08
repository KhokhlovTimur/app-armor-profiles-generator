from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QTextEdit, QWizardPage
)
from PyQt5.QtCore import Qt

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage
from src.util.apparmor_rules_reader import get_abstractions


class AbstractionsPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Абстракции (abstractions)")

        self.abstractions = get_abstractions()
        self.filtered_keys = list(self.abstractions.keys())

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Поиск по abstractions:"))

        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Введите часть имени...")
        layout.addWidget(self.search_line_edit)

        self.abstractions_list_widget = QListWidget()
        layout.addWidget(self.abstractions_list_widget)

        self.preview_text_edit = QTextEdit()
        self.preview_text_edit.setReadOnly(True)
        layout.addWidget(self.preview_text_edit)

        self.setLayout(layout)

        self.search_line_edit.textChanged.connect(self.filter_abstractions)
        self.abstractions_list_widget.itemClicked.connect(self.show_abstraction_content)

        self.populate_abstraction_list()

    def populate_abstraction_list(self):
        self.abstractions_list_widget.clear()
        for name in sorted(self.filtered_keys):
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.abstractions_list_widget.addItem(item)

    def filter_abstractions(self, text):
        text = text.lower()
        self.filtered_keys = [key for key in self.abstractions if text in key.lower()]
        self.populate_abstraction_list()

    def show_abstraction_content(self, item):
        name = item.text()
        content = self.abstractions.get(name, "")
        self.preview_text_edit.setPlainText(content)

    def get_profile_fragment(self) -> str:
        selected_includes = []
        for i in range(self.abstractions_list_widget.count()):
            item = self.abstractions_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_includes.append(item.text())

        if not selected_includes:
            return ""

        fragment = "  # abstractions\n"
        for name in selected_includes:
            fragment += f"  include <abstractions/{name}>\n"
        return fragment + "\n"
