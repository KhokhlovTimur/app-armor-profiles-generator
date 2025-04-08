import re
from typing import List

from PyQt5.QtWidgets import (
    QVBoxLayout, QTextEdit, QWizardPage, QMessageBox, QPushButton, QLabel, QWizard
)

from src.apparmor.apparmor_parser import validate_and_load_profile
from src.ui.profile_wizard.wizard_page import AppArmorWizardPage
from src.util.apparmor_util import extract_profile_name


class LastOptionsPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.pages: List[AppArmorWizardPage] = []

        layout = QVBoxLayout()
        self.preview_text_edit = QTextEdit()
        self.preview_text_edit.setReadOnly(True)
        layout.addWidget(self.preview_text_edit)

        self.setLayout(layout)

    def initializePage(self):
        super().initializePage()
        self.generate_preview()

        self.wizard().setOption(QWizard.HaveCustomButton1, True)
        self.wizard().setButtonText(QWizard.CustomButton1, "Save")
        self.wizard().button(QWizard.CustomButton1).clicked.connect(self.save_profile)

        self.wizard().setOption(QWizard.HaveCustomButton2, True)
        self.wizard().setButtonText(QWizard.CustomButton2, "Run in sandbox")
        self.wizard().button(QWizard.CustomButton2).clicked.connect(self.run_in_sandbox)

        self.wizard().setButtonLayout([
            QWizard.Stretch,
            QWizard.BackButton,
            QWizard.CustomButton1,
            QWizard.CustomButton2,
            QWizard.CancelButton,
        ])

    def cleanupPage(self):
        super().cleanupPage()

        self.wizard().setOption(QWizard.HaveCustomButton1, False)
        self.wizard().setOption(QWizard.HaveCustomButton2, False)

        self.wizard().setButtonLayout([
            QWizard.Stretch,
            QWizard.BackButton,
            QWizard.NextButton,
            QWizard.CancelButton,
        ])

    def run_in_sandbox(self):
        pass

    def generate_preview(self):
        self.pages = [self.wizard().page(pid) for pid in self.wizard().pageIds()]
        profile_text = ""
        fragments = []
        for page in self.pages:
            fragment = page.get_profile_fragment().strip()
            if fragment:
                fragments.append(fragment)

        full_profile_text = "\n\n".join(fragments)
        profile_text += full_profile_text

        profile_text += "\n}\n"

        self.preview_text_edit.setPlainText(profile_text)

    def save_profile(self):
        profile_data = self.preview_text_edit.toPlainText()
        try_save = validate_and_load_profile(profile_data, extract_profile_name(profile_data))
        if try_save.returncode == 0:
            QMessageBox.information(self, "Success", "Profile saved successfully")
        else:
            self.error_message = self.filter_stderr(
                try_save.stderr) if try_save.stderr else "Неизвестная ошибка при проверке профиля."
            QMessageBox.warning(self, "Ошибка", f"Ошибка в профиле:\n{self.error_message}")

    def create_page8(self):
        page = QWizardPage()
        page.setTitle("Шаг 8: Применение и тестирование профиля")
        layout = QVBoxLayout()

        label = QLabel("Нажмите кнопку, чтобы применить профиль.")
        layout.addWidget(label)

        applyButton = QPushButton("Применить профиль")
        layout.addWidget(applyButton)
        applyButton.clicked.connect(self.apply_profile)

        page.setLayout(layout)
        return page

    def filter_stderr(self, stderr: str) -> str:
        stderr = stderr.strip()
        stderr = re.sub(r'^\[sudo\] пароль для .*?:\s*', '', stderr)
        return stderr