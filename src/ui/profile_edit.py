from PyQt5.QtWidgets import QPushButton, QMessageBox

from src.apparmor.apparmor_manager import read_apparmor_profile_by_name
from src.apparmor.apparmor_parser import edit_profile_body_and_check
from src.model.apparmor_profile import AppArmorProfile
from src.ui.create_profile.profile_add import CreateProfilePage
from src.ui.page_holder import PagesHolder
from src.util.apparmor_util import extract_profile_path


class EditProfilePage(CreateProfilePage):
    def __init__(self, profile: AppArmorProfile, parent, is_custom_profile:bool=False):
        super().__init__(profile)
        self.setWindowTitle("Edit Profile")
        self.profile = profile
        self.edit_profile_text = None
        self.parent = parent
        self.is_custom_profile = is_custom_profile

        if not is_custom_profile:
            self.profile_code = read_apparmor_profile_by_name(self.profile.name)
        else:
            self.profile_code = profile.render()

        self.template_edit.setPlainText(self.profile_code)

    def go_back(self):
        self.deleteLater()
        PagesHolder().get_content_area().removeWidget(self)

    def save_profile(self, profile_as_string=None):
        if self.is_custom_profile:
            command = edit_profile_body_and_check(self.template_edit.toPlainText(), self.profile.name, self.profile.tunables)
        else:
            command = edit_profile_body_and_check(self.template_edit.toPlainText(), self.profile.name)
        self.check_profile(command)
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

        # self.import_file_button = QPushButton("Import", self)
        # self.import_file_button.clicked.connect(self.import_profile)
        # self.buttons_layout.addWidget(self.import_file_button)

        self.sandbox_button = QPushButton("Run In Sandbox", self)
        self.sandbox_button.clicked.connect(lambda: self._launch_app())
        self.buttons_layout.addWidget(self.sandbox_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_profile)
        self.buttons_layout.addWidget(self.save_button)

        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(self.go_back)
        self.buttons_layout.addWidget(self.back_button)

    def run_in_sandbox(self, bin_path, profile_as_string=None):
        super().run_in_sandbox(bin_path, self.template_edit.toPlainText())

    def _launch_app(self):
        path = extract_profile_path(self.template_edit.toPlainText())
        if path is None:
            QMessageBox.warning(self, "Error", "Binary not found")
            return
        self.run_in_sandbox(path)

    def _on_sandbox_finished(self):
        confirm = super()._on_sandbox_finished()
        if confirm == QMessageBox.Cancel:
            return
        self.deleteLater()
        PagesHolder().get_content_area().removeWidget(self)

