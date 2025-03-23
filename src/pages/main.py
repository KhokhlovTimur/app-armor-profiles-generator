import os
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QStackedWidget

from src.app_armor.credentials_holder import CredentialsHolder
from src.pages.add_profile import AddProfilePage
from src.pages.page_holder import PagesHolder
from src.pages.profiles import ProfilesPage
from src.pages.side_menu import SideMenu


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        holder = CredentialsHolder()
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
        self.profiles_page = ProfilesPage()
        holder.profiles = self.profiles_page.all_items
        self.add_profile_page = AddProfilePage()
        self.menu = SideMenu(self.add_profile_page)

        self.content_area.addWidget(self.profiles_page)
        self.content_area.addWidget(self.add_profile_page)

        menu_widget = self.menu.menu_widget

        self.main_layout.addWidget(menu_widget)
        self.main_layout.addWidget(self.menu.line)
        self.main_layout.addWidget(self.content_area)

        self.setLayout(self.main_layout)

if __name__ == '__main__':
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()