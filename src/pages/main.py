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
        menu = SideMenu()
        menu_widget = menu.menu_widget

        content_area = QStackedWidget()

        content_area.addWidget(ProfilesPage())
        content_area.addWidget(AddProfilePage())

        menu.profiles_button.clicked.connect(lambda: content_area.setCurrentIndex(0))
        menu.add_profile_button.clicked.connect(lambda: content_area.setCurrentIndex(1))

        self.main_layout.addWidget(menu_widget)
        self.main_layout.addWidget(menu.line)
        self.main_layout.addWidget(content_area)

        self.setLayout(self.main_layout)
        # load_stylesheet("side_menu.qss", self)

if __name__ == '__main__':
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()