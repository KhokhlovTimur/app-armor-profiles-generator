import os
from PyQt5.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QComboBox, QListWidget, QTextEdit, QCompleter
)

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage
from src.ui.util.path_completer import ExecutablePathCompleter
from src.util.apparmor_util import extract_profile_path, get_profile_path_from_file
from src.util.command_executor_util import run_command


class ExecuteRulesPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Переходы между профилями при выполнении (exec rules)")

        self.layout = QVBoxLayout()
        self.entries = []

        self.layout.addWidget(QLabel("Добавьте правила выполнения (ix, px, cx, ux, -> профиль, + профиль):"))

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Путь к исполняемому файлу")
        self.path_input.textChanged.connect(self.add_local_profile_name)

        completer = ExecutablePathCompleter(self.path_input, False)
        self.path_input.setCompleter(completer)
        self.path_input.textEdited.connect(completer.update_model)

        self.exec_mode_combo = QComboBox()
        self.exec_mode_combo.addItems([
            "px", "ix", "cx", "ux", "Px", "Cx", "Ux", "pix", "cix", "pux", "cux", "PUx", "CUx"
        ])

        self.named_profile_label = QLabel("Имя целевого профиля:")
        self.named_profile_input = QLineEdit()
        self.named_profile_input.setPlaceholderText("Имя целевого профиля")
        self.named_profile_input.textChanged.connect(self.add_local_profile_name)


        named_profile_layout = QVBoxLayout()
        named_profile_layout.addWidget(self.named_profile_label)
        named_profile_layout.addWidget(self.named_profile_input)

        self.stacked_profile_input = QLineEdit()
        self.stacked_profile_input.setPlaceholderText("+ Имя дополнительного профиля")

        self.add_button = QPushButton("Добавить правило")
        self.clear_button = QPushButton("Очистить список")

        self.entry_list = QListWidget()

        form = QHBoxLayout()
        form.addWidget(self.path_input)
        form.addWidget(self.exec_mode_combo)
        self.layout.addLayout(named_profile_layout)
        form.addWidget(self.stacked_profile_input)
        form.addWidget(self.add_button)
        form.addWidget(self.clear_button)

        self.layout.addLayout(form)
        self.layout.addWidget(self.entry_list)

        self.profile_map = {}
        profile_dir = "/etc/apparmor.d"
        if os.path.isdir(profile_dir):
            for file in os.listdir(profile_dir):
                full_path = os.path.join(profile_dir, file)
                if os.path.isfile(full_path):
                    self.profile_map[file] = full_path

        completer = QCompleter(self.profile_map.keys())
        completer.setCaseSensitivity(False)
        self.named_profile_input.setCompleter(completer)
        self.named_profile_input.textChanged.connect(self.show_profile_preview)

        self.child_profile_label = QLabel("Вложенный профиль:")
        self.child_profile_edit = QTextEdit()
        self.child_profile_edit.setPlaceholderText("profile /path/to/bin {\n  # правила\n}")
        self.child_profile_edit.hide()
        self.child_profile_label.hide()

        self.layout.addWidget(self.child_profile_label)
        self.layout.addWidget(self.child_profile_edit)

        self.profile_preview = QTextEdit()
        self.profile_preview.setReadOnly(True)
        self.profile_preview.setPlaceholderText("Предпросмотр выбранного профиля")
        self.layout.addWidget(self.profile_preview)

        self.add_button.clicked.connect(self.add_entry)
        self.clear_button.clicked.connect(self.clear_entries)

        self.exec_mode_combo.currentIndexChanged.connect(self.toggle_named_profile_field)

        self.setLayout(self.layout)

    def show_profile_preview(self, text):
        path = self.profile_map.get(text.strip())
        if "c" not in self.exec_mode_combo.currentText().lower() and path and os.path.isfile(path):
            try:
                result = run_command(['sudo','-S', 'cat', path])
                if result.returncode == 0:
                    self.profile_preview.setPlainText(result.stdout)
                else:
                    self.profile_preview.setPlainText("Ошибка: " + result.stderr)
            except Exception as e:
                self.profile_preview.setPlainText(f"Ошибка: {e}")
        else:
            self.profile_preview.clear()

    def add_local_profile_name(self):
        mode = self.exec_mode_combo.currentText()
        if "c" in mode.lower():
            if self.named_profile_input.text().strip():
                name = self.named_profile_input.text()
            else:
                name = self.path_input.text().strip()

            self.child_profile_edit.setPlainText(f"profile {name} " + "{\n  # rules\n}")

    def toggle_named_profile_field(self):
        mode = self.exec_mode_combo.currentText()
        is_ix = mode == "ix"
        is_child_mode = "c" in mode.lower()

        self.named_profile_input.setVisible(not is_ix)
        self.named_profile_label.setVisible(not is_ix)

        self.child_profile_edit.setVisible(is_child_mode)
        self.child_profile_label.setVisible(is_child_mode)

    def add_entry(self):
        path = self.path_input.text().strip()
        mode = self.exec_mode_combo.currentText()
        to_profile = get_profile_path_from_file(self.named_profile_input.text().strip())
        if "c" in mode.lower():
            to_profile = self.named_profile_input.text().strip()
        stacked = self.stacked_profile_input.text().strip()

        if not path or not mode:
            return

        rule = f"{path} {mode}"
        if to_profile:
            rule += f" -> {to_profile}"
        if stacked:
            rule += f" + {stacked}"
        rule += ","

        self.entry_list.addItem(rule)
        self.entries.append(rule)

        if "c" in mode.lower():
            child = self.child_profile_edit.toPlainText().strip()
            if child:
                self.entries.append(child)
                self.entry_list.addItem(child)

        self.path_input.clear()
        self.named_profile_input.clear()
        self.stacked_profile_input.clear()
        self.child_profile_edit.clear()

    def clear_entries(self):
        self.entry_list.clear()
        self.entries.clear()

    def get_profile_fragment(self):
        if not self.entries:
            return ""
        return "\n" + "\n".join(f"  {line}" for line in self.entries)
