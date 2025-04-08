from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QTextEdit
)
from PyQt5.QtCore import Qt

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage
from src.util.apparmor_rules_reader import get_tunables


class TunablesPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Tunables — системные переменные")

        self.tunables = get_tunables()
        self.filtered_keys = list(self.tunables.keys())

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Поиск по tunables:"))

        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Введите часть имени...")
        layout.addWidget(self.search_line_edit)

        self.tunables_list_widget = QListWidget()
        layout.addWidget(self.tunables_list_widget)

        self.preview_text_edit = QTextEdit()
        self.preview_text_edit.setReadOnly(True)
        layout.addWidget(self.preview_text_edit)

        self.setLayout(layout)

        self.search_line_edit.textChanged.connect(self.filter_tunables)
        self.tunables_list_widget.itemClicked.connect(self.show_tunable_content)

        self.populate_tunables_list()

    def populate_tunables_list(self):
        self.tunables_list_widget.clear()
        for name in sorted(self.filtered_keys):
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.tunables_list_widget.addItem(item)

    def filter_tunables(self, text):
        text = text.lower()
        self.filtered_keys = [key for key in self.tunables if text in key.lower()]
        self.populate_tunables_list()

    def show_tunable_content(self, item):
        name = item.text()
        content = self.tunables.get(name, "")
        self.preview_text_edit.setPlainText(content)

    def get_profile_fragment(self) -> str:
        selected = []
        for i in range(self.tunables_list_widget.count()):
            item = self.tunables_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())

        if not selected:
            return ""

        fragment = "\n"
        for name in selected:
            fragment += f"include <tunables/{name}>\n"
        return fragment

    def get_priority(self):
        return 100