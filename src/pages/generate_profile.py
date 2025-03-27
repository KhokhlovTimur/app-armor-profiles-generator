from PyQt5.QtWidgets import QStackedWidget, QWidget

from src.pages.page_holder import PagesHolder
from src.pages.generate_profile_items_stack import LogMonitorPage, ProfileDiffPage, ProfileManager, SelectGenerateProfilePage


class GenerateProfilePage(QWidget):
    def __init__(self):
        super().__init__()

    def init_stack(self) -> QStackedWidget:
        self.profile_mgr = ProfileManager()
        self.select_page = SelectGenerateProfilePage(self.profile_mgr)
        self.log_page = LogMonitorPage(self.profile_mgr)
        self.diff_page = ProfileDiffPage()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.select_page)
        self.stack.addWidget(self.log_page)
        self.stack.addWidget(self.diff_page)
        PagesHolder().get_content_area().addWidget(self.stack)
        PagesHolder().get_content_area().setCurrentWidget(self.stack)

        self.select_page.started.connect(lambda path, profile_name, start_time : self.on_profile_started(path, profile_name, start_time))
        self.log_page.profileReady.connect(self.on_profile_ready)
        self.log_page.back_pressed.connect(self.stack_back)
        self.diff_page.applyChanges.connect(self.on_apply_changes)

        return self.stack

    def on_profile_started(self, bin_path, profile_name, start_time):
        self.stack.setCurrentWidget(self.log_page)
        self.log_page.load_events_from_log(profile_name, start_time)

    def on_profile_ready(self, allow_rules, deny_rules):
        new_profile_text = self.profile_mgr.update_profile(allow_rules, deny_rules)
        self.diff_page.show_diff(new_profile_text if new_profile_text else "Ошибка генерации профиля")
        self.stack.setCurrentWidget(self.diff_page)

    def on_apply_changes(self):
        self.profile_mgr.load_profile_enforce()
        self.statusBar().showMessage("Профиль применен в enforce-режиме. Готово.")

    def stack_back(self):
        cur = self.stack.currentIndex()
        self.stack.setCurrentIndex(cur - 1)