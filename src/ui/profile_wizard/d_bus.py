from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QListWidget, QListWidgetItem
)
from src.ui.profile_wizard.wizard_page import AppArmorWizardPage


class DBusRulesPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("D-Bus правила (dbus)")

        self.layout = QVBoxLayout()
        self.entries = []

        self.layout.addWidget(QLabel("Добавьте правила доступа к D-Bus (bus, dest, interface, method, path, perms):"))

        self.entry_list = QListWidget()
        self.layout.addWidget(self.entry_list)

        form_layout = QHBoxLayout()

        self.bus_input = QComboBox()
        self.bus_input.addItems(["", "system", "session"])

        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("com.example.Destination")

        self.interface_input = QLineEdit()
        self.interface_input.setPlaceholderText("com.example.Interface")

        self.method_input = QLineEdit()
        self.method_input.setPlaceholderText("MethodName")

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("/object/path")

        self.perms_input = QLineEdit()
        self.perms_input.setPlaceholderText("send, receive")

        add_button = QPushButton("Добавить правило")
        add_button.clicked.connect(self.add_entry)

        form_layout.addWidget(QLabel("bus:"))
        form_layout.addWidget(self.bus_input)
        form_layout.addWidget(QLabel("dest:"))
        form_layout.addWidget(self.dest_input)
        form_layout.addWidget(QLabel("interface:"))
        form_layout.addWidget(self.interface_input)
        form_layout.addWidget(QLabel("method:"))
        form_layout.addWidget(self.method_input)
        form_layout.addWidget(QLabel("path:"))
        form_layout.addWidget(self.path_input)
        form_layout.addWidget(QLabel("perms:"))
        form_layout.addWidget(self.perms_input)
        form_layout.addWidget(add_button)

        self.layout.addLayout(form_layout)

        self.setLayout(self.layout)

    def add_entry(self):
        parts = ["dbus"]

        bus = self.bus_input.currentText().strip()
        dest = self.dest_input.text().strip()
        interface = self.interface_input.text().strip()
        method = self.method_input.text().strip()
        path = self.path_input.text().strip()
        perms = self.perms_input.text().strip()

        if bus:
            parts.append(f"bus={bus}")
        if dest:
            parts.append(f"dest={dest}")
        if path:
            parts.append(f"path={path}")
        if interface:
            parts.append(f"interface={interface}")
        if method:
            parts.append(f"method={method}")
        if perms:
            if "," in perms or " " in perms:
                parts.append(f"({perms})")
            else:
                parts.append(perms)

        rule = " ".join(parts) + ","
        self.entry_list.addItem(rule)
        self.entries.append(rule)

        self.bus_input.setCurrentIndex(0)
        self.dest_input.clear()
        self.interface_input.clear()
        self.method_input.clear()
        self.path_input.clear()
        self.perms_input.clear()

    def get_profile_fragment(self):
        if not self.entries:
            return ""
        return "\n" + "\n".join(f"  {line}" for line in self.entries)
