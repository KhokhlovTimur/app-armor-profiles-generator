from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QComboBox, QListWidget, QLabel, QVBoxLayout, QPushButton

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage


class MountRulesPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Правила монтирования (mount / umount / remount / pivot_root)")

        self.layout = QVBoxLayout()
        self.entries = []

        self.layout.addWidget(QLabel("Добавьте mount-правила:"))

        # Выбор действия
        self.action_combo = QComboBox()
        self.action_combo.addItems(["mount", "remount", "umount", "pivot_root"])

        # fstype и options
        self.fstype_input = QLineEdit()
        self.fstype_input.setPlaceholderText("fstype=... или fstype in (...)")

        self.options_input = QLineEdit()
        self.options_input.setPlaceholderText("options=ro или options in (ro, nodev)")

        # source и destination
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Источник (например, /dev/sda1, none)")

        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Куда монтировать → /mnt/**")

        # профиль при pivot_root
        self.profile_input = QLineEdit()
        self.profile_input.setPlaceholderText("→ имя профиля (только для pivot_root)")

        # кнопки
        self.add_button = QPushButton("Добавить правило")
        self.clear_button = QPushButton("Очистить список")
        self.entry_list = QListWidget()

        self.add_button.clicked.connect(self.add_entry)
        self.clear_button.clicked.connect(self.clear_entries)

        self.layout.addWidget(QLabel("Тип действия:"))
        self.layout.addWidget(self.action_combo)
        self.layout.addWidget(QLabel("fstype (необязательно):"))
        self.layout.addWidget(self.fstype_input)
        self.layout.addWidget(QLabel("options (необязательно):"))
        self.layout.addWidget(self.options_input)
        self.layout.addWidget(QLabel("Источник (source):"))
        self.layout.addWidget(self.source_input)
        self.layout.addWidget(QLabel("Точка монтирования (→ destination):"))
        self.layout.addWidget(self.dest_input)
        self.layout.addWidget(QLabel("Профиль при pivot_root (необязательно):"))
        self.layout.addWidget(self.profile_input)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.entry_list)

        self.setLayout(self.layout)

    def add_entry(self):
        action = self.action_combo.currentText().strip()
        fstype = self.fstype_input.text().strip()
        options = self.options_input.text().strip()
        source = self.source_input.text().strip()
        dest = self.dest_input.text().strip()
        profile = self.profile_input.text().strip()

        parts = []

        if action == "pivot_root":
            parts.append("pivot_root")
            if source:
                parts.append(source)
            if dest:
                parts.append(dest)
            if profile:
                parts.append(f"-> {profile}")
        else:
            parts.append(action)
            if fstype:
                parts.append(f"fstype=({fstype})")
            if options:
                parts.append(f"options=({options})")
            if source:
                parts.append(source)
            if dest:
                parts.append(f"-> {dest}")

        rule = " ".join(parts) + ","
        self.entry_list.addItem(rule)
        self.entries.append(rule)

        # Очистка
        self.fstype_input.clear()
        self.options_input.clear()
        self.source_input.clear()
        self.dest_input.clear()
        self.profile_input.clear()

    def clear_entries(self):
        self.entry_list.clear()
        self.entries.clear()

    def get_profile_fragment(self):
        if not self.entries:
            return ""
        return "\n" + "\n".join(f"  {line}" for line in self.entries)