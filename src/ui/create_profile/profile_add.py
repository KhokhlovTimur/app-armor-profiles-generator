import re

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit, QPushButton, QHBoxLayout, QSplitter, QWidget, QDialog, \
    QMessageBox, QComboBox, QLineEdit, QFormLayout, QDialogButtonBox, QTableWidgetItem, QSizePolicy, \
    QHeaderView, QTableWidget, QStackedWidget

from src.apparmor.apparmor_parser import TMP_PROFILE_NAME, edit_profile_body_and_check
from src.model.apparmor_profile import AppArmorProfile
from src.ui.create_profile.profile_page_template import ProfilePageTemplate, LineNumberArea
from src.ui.executable import ExecutablePage
from src.ui.util.custom_console import SandboxConsole
from src.ui.util.path_completer import ExecutablePathCompleter
from src.util.apparmor_util import replace_profile_body_from_string, parse_profile_rules, profile_name_from_path
from src.util.command_executor_util import launch_command_interactive
from src.util.file_util import load_stylesheet, join_project_root, load_stylesheet_buttons


class CreateProfilePage(ProfilePageTemplate, ExecutablePage):
    # profile_template_path = join_project_root("resources", "profile_template.txt")
    __profile_styles = "add_profile_page.qss"
    _tmp_profile_name = "tmp_profile"
    _instance = None

    @classmethod
    def instance(cls, profile: AppArmorProfile):
        if cls._instance is None:
            cls._instance = cls(profile)
        return cls._instance

    def __init__(self, profile: AppArmorProfile = None):
        super().__init__()
        self.setWindowTitle("New Profile")
        self.setGeometry(200, 200, 400, 300)

        self.code_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        self.template_edit = QPlainTextEdit()
        self.template_edit.setObjectName("edit_text_area")
        load_stylesheet(self.__profile_styles, self.template_edit)
        self.profile = profile
        if self.profile.path is not None and len(self.profile.name.strip()) == 0:
            self.profile.name = ""
        self.profile_code = self.profile.render()
        if self.profile.path is not None and len(self.profile.name.strip()) == 0:
            self.profile.name = profile_name_from_path(profile.path)
        self.template_edit.setPlainText(self.profile_code)
        self.template_edit.setPlaceholderText("Enter or edit template...")

        self.view_mode_selector = QComboBox()
        self.view_mode_selector.addItems(["Code View", "Table View"])
        self.view_mode_selector.setFixedWidth(150)
        load_stylesheet("combobox.qss", self.view_mode_selector)
        self.view_mode_selector.currentIndexChanged.connect(self.toggle_view_mode)
        self.code_layout.insertWidget(0, self.view_mode_selector)
        self.rules_table = None

        btns_layout = QHBoxLayout()
        self.add_rule_btn = QPushButton("Add Rule")
        load_stylesheet_buttons(self.add_rule_btn)
        self.remove_rule_btn = QPushButton("Remove Selected")
        load_stylesheet_buttons(self.remove_rule_btn)
        btns_layout.addWidget(self.add_rule_btn)
        btns_layout.addWidget(self.remove_rule_btn)

        self.add_rule_btn.clicked.connect(self.add_rule_row)
        self.remove_rule_btn.clicked.connect(self.remove_selected_rows)
        self.code_layout.insertLayout(1, btns_layout)

        self.toggle_view_mode(0)

        self.line_number_area = LineNumberArea(self.template_edit)

        splitter.addWidget(self.line_number_area)
        splitter.addWidget(self.template_edit)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.code_layout.addWidget(splitter, stretch=1)

        self.buttons_layout = QHBoxLayout()
        self._add_buttons()
        self.buttons_container: QWidget = QWidget()
        self.buttons_container.setLayout(self.buttons_layout)

        load_stylesheet("buttons.qss", self.buttons_container)

        self.code_layout.addStretch()
        self.code_layout.addWidget(self.buttons_container)

        self.setLayout(self.code_layout)

        self.template_edit.textChanged.connect(self.update_line_numbers)

    def update_line_numbers(self):
        self.template_edit.blockSignals(True)
        try:
            self.line_number_area.update_area()
            self.highlight_changes()
        finally:
            self.template_edit.blockSignals(False)

    def select_file(self):
        path = super().select_file()
        if path is not None:
            self.profile.name = self.file_path.split('/')[-1]
            self.profile.path = self.file_path
            self.template_edit.setPlainText(self.profile.render())

    def _add_buttons(self):
        self.increase_font_button = QPushButton("Increase font size", self)
        self.increase_font_button.clicked.connect(self.increase_font_size)
        self.buttons_layout.addWidget(self.increase_font_button)

        self.decrease_font_button = QPushButton("Decrease font size", self)
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        self.buttons_layout.addWidget(self.decrease_font_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(lambda: self.save_profile())
        self.buttons_layout.addWidget(self.save_button)

        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(lambda: self.back())
        self.buttons_layout.addWidget(self.back_button)

    def save_profile(self, profile_as_string: str = None):
        super().save_profile(profile_as_string)
        if self.error_message is None:
            self.back()

    def back(self):
        self.finished.emit()
        self.deleteLater()

    def run_in_sandbox(self, bin_path, profile_as_string=None):
        output = edit_profile_body_and_check(self.template_edit.toPlainText(), TMP_PROFILE_NAME)
        self.check_profile(output, profile_as_string, "Successful check.")

        if output.returncode != 0:
            self.error_message = self.filter_stderr(
                output.stderr) if output.stderr else "Неизвестная ошибка при проверке профиля."
            QMessageBox.warning(self, "Error", f"{self.error_message}")
            return

        self.console = SandboxConsole()
        self.console.run_script(self, exec_func=self._on_sandbox_finished)

    def toggle_view_mode(self, index):
        if index == 0:
            if self.rules_table:
                self.sync_code_from_table()
                self.template_edit.setPlainText(self.profile_code)
            self.template_edit.setVisible(True)
            if hasattr(self, 'line_number_area'):
                self.line_number_area.setVisible(True)
            self.add_rule_btn.setVisible(False)
            self.remove_rule_btn.setVisible(False)
            if self.rules_table:
                self.code_layout.removeWidget(self.rules_table)
                self.rules_table.deleteLater()
                self.rules_table = None
        elif index == 1:
            self.sync_code_from_text()
            self.template_edit.setVisible(False)
            if hasattr(self, 'line_number_area'):
                self.line_number_area.setVisible(False)
            self.add_rule_btn.setVisible(True)
            self.remove_rule_btn.setVisible(True)
            self.show_table_view()

    def _on_sandbox_finished(self) -> QMessageBox:
        confirm = QMessageBox.question(
            self,
            "Save changes?",
            "Save changes?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )

        if confirm == QMessageBox.Save:
            self.save_profile()
        elif confirm == QMessageBox.Discard:
            print("Изменения не сохранены.")
        else:
            print("Действие отменено.")

        return confirm


    def show_table_view(self):
        rule_re = re.compile(r'^(?P<path>[^\s]+)\s+(?P<perms>[a-zA-Zx]+),?$')
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(2)
        self.rules_table.setHorizontalHeaderLabels(["Path / Rule", "Permissions"])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rules_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.rules_table.setMinimumHeight(200)
        self.rules_table.setStyleSheet("font-family: monospace; font-size: 12px;")

        for line in self.profile_code.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("profile ") or line in ("{", "}"):
                continue

            if line.startswith("include "):
                path = line
                perms = ""
            else:
                match = rule_re.match(line)
                if match:
                    path = match.group("path")
                    perms = match.group("perms")
                else:
                    path = line
                    perms = ""

            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            self.rules_table.setItem(row, 0, QTableWidgetItem(path))
            self.rules_table.setItem(row, 1, QTableWidgetItem(perms))

        self.code_layout.insertWidget(2, self.rules_table, stretch=1)

    def add_rule_row(self):
        dialog = AddRuleDialog()
        if dialog.exec_() == QDialog.Accepted:
            path, perms = dialog.get_data()
            if path:
                self.profile.parse()
                row = self.rules_table.rowCount()
                self.rules_table.insertRow(row)
                self.rules_table.setItem(row, 0, QTableWidgetItem(path))
                self.rules_table.setItem(row, 1, QTableWidgetItem(perms))
                self.profile.all_rules.append(f'{path} {perms}')

                self.sync_code_from_table()

    def remove_selected_rows(self):
        if not self.rules_table:
            return

        selected_indexes = self.rules_table.selectionModel().selectedIndexes()

        if not selected_indexes:
            QMessageBox.information(self, "Info", "No rows selected.")
            return

        selected_rows = sorted({index.row() for index in selected_indexes}, reverse=True)

        for row in selected_rows:
            self.rules_table.removeRow(row)
            self.profile.all_rules.remove()

        self.sync_code_from_table()

    def convert_table_to_profile(self):
        lines = []
        for row in range(self.rules_table.rowCount()):
            path_item = self.rules_table.item(row, 0)
            perms_item = self.rules_table.item(row, 1)

            path = path_item.text().strip() if path_item else ""
            perms = perms_item.text().strip() if perms_item else ""

            if not path:
                continue

            if perms:
                line = f"{path} {perms},"
            else:
                line = f"{path},"

            lines.append(line)

        body = "\n".join(lines)

        full_text = replace_profile_body_from_string(
            self.template_edit.toPlainText(), body
        )
        return full_text

    def sync_code_from_text(self):
        self.profile_code = self.template_edit.toPlainText()

    def sync_code_from_table(self):
        # self.profile_code = self.convert_table_to_profile()
        self.profile.parse()
        self.profile_code = self.profile.render()
        self.template_edit.setPlainText(self.profile_code)


    def highlight_changes(self, edited_text=None):
        if edited_text is None:
            edited_text = self.template_edit.toPlainText()
        changed_lines = self.get_changed_lines(self.profile_code, edited_text)
        changed_lines = sorted(set(changed_lines))

        cursor = self.template_edit.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.endEditBlock()

        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#ffffaa"))

        doc = self.template_edit.document()

        seen_texts = set()
        shift = 0
        adjusted_lines = []

        for i, line_num in enumerate(changed_lines):
            adjusted_line_num = line_num + shift
            block = doc.findBlockByLineNumber(adjusted_line_num)
            text = block.text()

            if text in seen_texts:
                shift += 1
                adjusted_line_num += 1
            else:
                seen_texts.add(text)

            adjusted_lines.append(adjusted_line_num)

        for line_num in adjusted_lines:
            block = doc.findBlockByLineNumber(line_num)
            if not block.isValid():
                continue
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            cursor.setCharFormat(fmt)

    def get_changed_lines(self, original_text: str, modified_text: str) -> list[int]:
        original_lines = original_text.strip().splitlines()
        modified_lines = modified_text.strip().splitlines()

        max_len = max(len(original_lines), len(modified_lines))
        changed = []

        for i in range(max_len):
            orig = original_lines[i] if i < len(original_lines) else ""
            mod = modified_lines[i] if i < len(modified_lines) else ""
            if orig.strip() != mod.strip() and mod not in original_lines:
                changed.append(i)
        return changed


class AddRuleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Rule")
        self.setMinimumWidth(300)

        self.path_input = QLineEdit()
        self.perms_input = QLineEdit()

        layout = QFormLayout(self)
        layout.addRow("Path / Rule:", self.path_input)
        layout.addRow("Permissions:", self.perms_input)

        self.completer = ExecutablePathCompleter(self.path_input, only_binaries=False)
        self.path_input.setCompleter(self.completer)
        self.path_input.textEdited.connect(self.completer.update_model)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self):
        return self.path_input.text().strip(), self.perms_input.text().strip()
