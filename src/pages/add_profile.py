import shutil
import subprocess

from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit, QPushButton, QHBoxLayout, QSplitter, QWidget, QDialog, QLabel, \
    QProgressBar, QMessageBox

from src.apparmor.apparmor_parser import tmp_profile_name, edit_profile_body_and_check
from src.pages.profile_page_template import ProfilePageTemplate, LineNumberArea
from src.util.command_executor_util import launch_command_interactive
from src.util.file_util import load_stylesheet, join_project_root


class AddProfilePage(ProfilePageTemplate):
    profile_template_path = join_project_root("resources", "profile_template.txt")
    __profile_styles = "add_profile_page.qss"
    _tmp_profile_name = "tmp_profile"
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Profile")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        self.template_edit = QPlainTextEdit()
        self.template_edit.setObjectName("edit_text_area")
        load_stylesheet(self.__profile_styles, self.template_edit)
        self.template_edit.setPlainText(self.get_default_template())
        self.template_edit.setPlaceholderText("Enter or edit template...")

        self.line_number_area = LineNumberArea(self.template_edit)

        splitter.addWidget(self.line_number_area)
        splitter.addWidget(self.template_edit)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, stretch=1)

        self.buttons_layout = QHBoxLayout()
        self._add_buttons()
        self.buttons_container: QWidget = QWidget()
        self.buttons_container.setLayout(self.buttons_layout)

        load_stylesheet("buttons.qss", self.buttons_container)

        layout.addStretch()
        layout.addWidget(self.buttons_container)

        self.setLayout(layout)

        self.template_edit.textChanged.connect(self.update_line_numbers)

    def select_file(self):
        path = super().select_file()
        if path is not None:
            base = self.get_default_template()
            new = base.replace("${profile_name}", self.file_path.split('/')[-1]).replace("${profile_path}",
                                                                                 self.file_path)
            self.template_edit.setPlainText(new)

    def get_default_template(self):
        return ''.join(open(AddProfilePage.profile_template_path).readlines())

    def _add_buttons(self):
        self.increase_font_button = QPushButton("Increase font size", self)
        self.increase_font_button.clicked.connect(self.increase_font_size)
        self.buttons_layout.addWidget(self.increase_font_button)

        self.decrease_font_button = QPushButton("Decrease font size", self)
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        self.buttons_layout.addWidget(self.decrease_font_button)

        self.select_file_button = QPushButton("Choose file for profile", self)
        self.select_file_button.clicked.connect(self.select_file)
        self.buttons_layout.addWidget(self.select_file_button)

        self.import_file_button = QPushButton("Import", self)
        self.import_file_button.clicked.connect(self.import_profile)
        self.buttons_layout.addWidget(self.import_file_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_profile)
        self.buttons_layout.addWidget(self.save_button)

    def launch_profile_interactive(self, bin_path, profile_as_string=None):
        output = edit_profile_body_and_check(self.template_edit.toPlainText(), tmp_profile_name)
        self._check_profile(output, profile_as_string)

        if output.returncode != 0:
            self.error_message = self.filter_stderr(output.stderr) if output.stderr else "Неизвестная ошибка при проверке профиля."
            QMessageBox.warning(self, "Error", f"{self.error_message}")
            return

        launch_command_interactive(f"aa-exec -p {tmp_profile_name} -- {bin_path}; exec bash", self)

        confirm = QMessageBox.question(
            self,
            "Сохранить изменения?",
            "Сохранить изменения в профиль?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )

        if confirm == QMessageBox.Save:
            self.save_profile()
        elif confirm == QMessageBox.Discard:
            print("Изменения не сохранены.")
        else:
            print("Действие отменено.")
