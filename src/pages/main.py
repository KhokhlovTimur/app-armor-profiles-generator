from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QStackedWidget

from src.app_armor.data_holder import DataHolder
from src.pages.add_profile_page import AddProfilePage
from src.pages.profiles_page import ProfilesPage
from src.pages.side_menu import SideMenu


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        holder = DataHolder()
        self.setWindowTitle("AppArmor GUI")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QHBoxLayout(self)
        self.menu = SideMenu()
        menu_widget = self.menu.menu_widget

        self.content_area = QStackedWidget()
        self.profiles_page = ProfilesPage()
        self.add_profile_page = AddProfilePage()

        self.content_area.addWidget(self.profiles_page)
        self.content_area.addWidget(self.add_profile_page)

        self.menu.profiles_button.clicked.connect(self.__on_menu_button_click)
        self.menu.add_profile_button.clicked.connect(self.__on_menu_button_click)
        self.menu.menu_button3.clicked.connect(self.__on_menu_button_click)

        self.main_layout.addWidget(menu_widget)
        self.main_layout.addWidget(self.menu.line)
        self.main_layout.addWidget(self.content_area)

        self.setLayout(self.main_layout)

    def __on_menu_button_click(self):
        event = self.sender()
        # if self.menu.buttons[event] == 0:
        #     self.profiles_page.display_profiles(None)

        if self.menu.buttons[event] == 1:
            self.add_profile_page.start_create_profile()

        for button in self.menu.buttons:
            if button != event:
                button.setChecked(False)

        event.setChecked(True)
        self.content_area.setCurrentIndex(event.property("index"))

if __name__ == '__main__':
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()