from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox, QStackedWidget)

from src.apparmor.apparmor_parser import filter_stderr
from src.apparmor.generator.generate_process_builder import Generator
from src.model.apparmor_profile import AppArmorProfile
from src.ui.create_profile.profile_add import CreateProfilePage
from src.ui.profile_edit import EditProfilePage
from src.util.apparmor_util import profile_name_from_path
from src.util.file_util import load_stylesheet_buttons
from src.ui.util.path_completer import ExecutablePathCompleter


class SelectGenerateProfilePage(QWidget):
    started = pyqtSignal(str, str, str)

    def __init__(self, stack: QStackedWidget, bin_path=None):
        super().__init__()
        self.bin_path = bin_path
        self.stack = stack

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        instr = QLabel("Укажите путь к программе для профилирования:")
        self.path_edit = QLineEdit()
        self.completer = ExecutablePathCompleter(self.path_edit, False)
        self.path_edit.setCompleter(self.completer)
        self.path_edit.textEdited.connect(self.completer.update_model)
        if bin_path is not None:
            self.path_edit.setText(bin_path)

        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_file)

        start_generate_btn = QPushButton("Generate profile")
        start_create_btn = QPushButton("Create Profile")
        load_stylesheet_buttons(start_generate_btn)
        load_stylesheet_buttons(start_create_btn)

        start_generate_btn.clicked.connect(self.on_start_generate)
        start_create_btn.clicked.connect(self.on_start_create)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)

        layout.addWidget(instr)
        layout.addLayout(path_layout)
        button_layout = QHBoxLayout()
        button_layout.addWidget(start_create_btn)
        button_layout.addWidget(start_generate_btn)

        layout.addLayout(button_layout)

        self.import_file_button = QPushButton("Import", self)
        self.import_file_button.clicked.connect(self.import_profile)
        load_stylesheet_buttons(self.import_file_button)
        layout.addWidget(self.import_file_button)

        layout.addStretch()
        self.setLayout(layout)

    def set_binary_path(self, path):
        self.path_edit.setText(path)

    def browse_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setNameFilter("Все файлы (*.*)")
        file_dialog.setViewMode(QFileDialog.List)

        if file_dialog.exec_():
            self.file_path = file_dialog.selectedFiles()[0]
            print(f"Выбран путь и файл: {self.file_path}")
            selected_file = file_dialog.selectedFiles()[0]
            self.path_edit.setText(selected_file)

    def on_start_generate(self):
        if not self.path_edit.text().strip():
            QMessageBox.warning(self, "Ошибка ввода", "Пожалуйста, выберите приложение.")
            return

        # self.generator_page = GeneratorPage(self.path_edit.text())
        # self.stack.addWidget(self.generator_page)
        # self.stack.setCurrentWidget(self.generator_page)
        # self.generator_page.finished.connect(self.stack_back)

        gen = Generator()
        res = gen.start_generate(self.path_edit.text())
        if res.returncode != 0:
            self.error_message = filter_stderr(
                res.stderr) if res.stderr else "Неизвестная ошибка при проверке профиля."
            QMessageBox.warning(self, "Error", f"{self.error_message}")
            return
        gen.exec_app(self)
        includes, abstractions, rules = gen.run_generate()
        self.generator_page = EditProfilePage(AppArmorProfile(path=self.path_edit.text(), tunables=includes, includes=abstractions, all_rules=rules), self, True)
        self.stack.addWidget(self.generator_page)
        self.stack.setCurrentWidget(self.generator_page)
        self.generator_page.finished.connect(self.stack_back)

    def on_start_create(self):
        if not self.path_edit.text().strip():
            QMessageBox.warning(self, "Ошибка ввода", "Пожалуйста, выберите приложение.")
            return

        profile = AppArmorProfile(path=self.path_edit.text())
        self.create_page = CreateProfilePage(profile)
        self.stack.addWidget(self.create_page)
        self.stack.setCurrentWidget(self.create_page)
        self.create_page.finished.connect(self.stack_back)

    def stack_back(self):
        cur = self.stack.currentIndex()
        self.stack.setCurrentIndex(cur - 1)

    def import_profile(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setNameFilter("Все файлы (*)")
        file_dialog.setViewMode(QFileDialog.List)

        if file_dialog.exec_():
            self.file_path = file_dialog.selectedFiles()[0]
            print(f"Выбран путь и файл: {self.file_path}")
            if self.file_path:
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        profile = AppArmorProfile(full_code=content)
                        self.create_page = CreateProfilePage(profile)
                        self.stack.addWidget(self.create_page)
                        self.stack.setCurrentWidget(self.create_page)
                        self.create_page.finished.connect(self.stack_back)
                        # self.template_edit.setPlainText(content)
                except Exception as e:
                    print(f"Ошибка при чтении файла: {e}")

        return None


class ProfileDiffPage(QWidget):
    applyChanges = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Предпросмотр нового профиля:"))
        self.diff_edit = QTextEdit()
        self.diff_edit.setReadOnly(True)
        layout.addWidget(self.diff_edit)
        apply_btn = QPushButton("Применить профиль")
        apply_btn.clicked.connect(lambda: self.applyChanges.emit())
        layout.addWidget(apply_btn)
        self.setLayout(layout)
