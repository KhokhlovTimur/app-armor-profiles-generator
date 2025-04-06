#!/usr/bin/env python3

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QStackedWidget

from src.apparmor.apparmor_parser import load_tmp_profile
from src.apparmor.credentials_holder import CredentialsHolder
from src.pages.apparmor_status import AppArmorStatusPage
from src.pages.create_profile.profile_create_start import StartGenerateProfilePage
from src.pages.new_binaries import NewBinariesHandler, NewBinariesPage
from src.pages.page_holder import PagesHolder
from src.pages.profile_constructor import ProfileGeneratorWidget
from src.pages.profiles import ProfilesPage
from src.pages.side_menu import SideMenu
from src.util.binary_watcher import Worker


class MainWindow(QWidget):
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        holder = CredentialsHolder()
        load_tmp_profile()
        self.setWindowTitle("AppArmor GUI")
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width, screen_height = screen_geometry.width(), screen_geometry.height()

        window_width, window_height = int(screen_width // 1.5), int(screen_height // 1.5)

        self.setGeometry(
            (screen_width - window_width) // 2,
            (screen_height - window_height) // 2,
            window_width,
            window_height
        )

        self.content_area = QStackedWidget()
        holder = PagesHolder()
        holder.content_area = self.content_area

        self.main_layout = QHBoxLayout(self)
        self.apparmor_status_page = AppArmorStatusPage()
        self.profiles_page = ProfilesPage()
        holder.profiles = self.profiles_page.all_items
        # self.add_profile_page = AddProfilePage()
        self.menu = SideMenu.instance()
        holder.side_menu = self.menu
        self.generator_page = StartGenerateProfilePage()
        self.new_binaries_page = NewBinariesPage(self.generator_page)
        self.constructor = ProfileGeneratorWidget()

        self.content_area.addWidget(self.apparmor_status_page)
        self.content_area.addWidget(self.profiles_page)
        # self.content_area.addWidget(self.add_profile_page)
        self.content_area.addWidget(self.new_binaries_page)
        self.content_area.addWidget(self.generator_page.stack)
        self.content_area.addWidget(self.constructor)

        menu_widget = self.menu.menu_widget

        self.main_layout.addWidget(menu_widget)
        self.main_layout.addWidget(self.menu.line)
        self.main_layout.addWidget(self.content_area)

        self.setLayout(self.main_layout)

        self.worker = Worker()
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.worker.newBinary.connect(lambda path, source: NewBinariesHandler().add_binary(self, self.generator_page, path, source))
        self.thread.started.connect(self.worker.start_monitoring)
        self.thread.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "banner") and self.banner:
            margin = 12
            self.banner.move(self.width() - self.banner.width() - margin, margin)

if __name__ == '__main__':
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()