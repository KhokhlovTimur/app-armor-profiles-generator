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

        self.searchLineEdit = QLineEdit()
        self.searchLineEdit.setPlaceholderText("Введите часть имени...")
        layout.addWidget(self.searchLineEdit)

        self.tunablesListWidget = QListWidget()
        layout.addWidget(self.tunablesListWidget)

        self.previewTextEdit = QTextEdit()
        self.previewTextEdit.setReadOnly(True)
        layout.addWidget(self.previewTextEdit)

        self.setLayout(layout)

        self.searchLineEdit.textChanged.connect(self.filterTunables)
        self.tunablesListWidget.itemClicked.connect(self.showTunableContent)

        self.populateTunablesList()

    def populateTunablesList(self):
        self.tunablesListWidget.clear()
        for name in sorted(self.filtered_keys):
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.tunablesListWidget.addItem(item)

    def filterTunables(self, text):
        text = text.lower()
        self.filtered_keys = [key for key in self.tunables if text in key.lower()]
        self.populateTunablesList()

    def showTunableContent(self, item):
        name = item.text()
        content = self.tunables.get(name, "")
        self.previewTextEdit.setPlainText(content)

    def get_profile_fragment(self) -> str:
        selected = []
        for i in range(self.tunablesListWidget.count()):
            item = self.tunablesListWidget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())

        if not selected:
            return ""

        fragment = "  # Используемые tunables\n"
        for name in selected:
            fragment += f"  #include <tunables/{name}>\n"
        return fragment