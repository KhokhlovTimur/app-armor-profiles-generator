from PyQt5 import Qt
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QPushButton, QDialog, QVBoxLayout, QLabel, QProgressBar

from src.apparmor.apparmor_manager import AppArmorManager
from src.apparmor.apparmor_parser import edit_profile_body_and_check
from src.pages.add_profile import AddProfilePage
from src.pages.page_holder import PagesHolder
from src.util.apparmor_util import extract_profile_body, extract_profile_path


class EditProfilePage(AddProfilePage):
    def __init__(self, profile_data, parent):
        super().__init__()
        self.setWindowTitle("Edit Profile")
        self.app_armor_manager = AppArmorManager()
        self.profile_data = profile_data
        self.parent = parent
        self.template_edit.setPlainText(self.app_armor_manager.read_apparmor_profile_by_name(self.profile_data['name']))

    def go_back(self):
        self.deleteLater()
        PagesHolder().get_content_area().removeWidget(self)

    def save_profile(self, profile_as_string=None):
        command = edit_profile_body_and_check(self.template_edit.toPlainText(), self.profile_data['name'])
        self._check_profile(command)
        if self.error_message is None:
            PagesHolder().get_content_area().setCurrentWidget(self.parent)
            self.deleteLater()
            PagesHolder().get_content_area().removeWidget(self)

    def _add_buttons(self):
        self.increase_font_button = QPushButton("Increase font size", self)
        self.increase_font_button.clicked.connect(self.increase_font_size)
        self.buttons_layout.addWidget(self.increase_font_button)

        self.decrease_font_button = QPushButton("Decrease font size", self)
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        self.buttons_layout.addWidget(self.decrease_font_button)

        self.import_file_button = QPushButton("Import", self)
        self.import_file_button.clicked.connect(self.import_profile)
        self.buttons_layout.addWidget(self.import_file_button)

        self.sandbox_button = QPushButton("Run In Sandbox", self)
        self.sandbox_button.clicked.connect(lambda: (
            self.launch_profile_interactive(extract_profile_path(self.template_edit.toPlainText())),
            self.deleteLater(),
            PagesHolder().get_content_area().removeWidget(self)
        ))
        self.buttons_layout.addWidget(self.sandbox_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_profile)
        self.buttons_layout.addWidget(self.save_button)

        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(self.go_back)
        self.buttons_layout.addWidget(self.back_button)

    def launch_profile_interactive(self, bin_path, profile_as_string=None):
        super().launch_profile_interactive(bin_path, self.template_edit.toPlainText())
