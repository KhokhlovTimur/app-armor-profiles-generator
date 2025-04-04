from PyQt5.QtWidgets import QStackedWidget, QWidget

from src.pages.create_profile.select_binary import SelectGenerateProfilePage

class StartGenerateProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_stack()

    def init_stack(self, bin_path=None) -> QStackedWidget:
        self.stack = QStackedWidget()
        self.select_page = SelectGenerateProfilePage(self.stack, bin_path)
        self.stack.addWidget(self.select_page)

        return self.stack

    def on_profile_ready(self, allow_rules, deny_rules):
        new_profile_text = self.profile_mgr.update_profile(allow_rules, deny_rules)
        self.diff_page.show_diff(new_profile_text if new_profile_text else "Ошибка генерации профиля")
        self.stack.setCurrentWidget(self.diff_page)

    def on_apply_changes(self):
        self.profile_mgr.load_profile_enforce()
        self.statusBar().showMessage("Профиль применен в enforce-режиме. Готово.")
