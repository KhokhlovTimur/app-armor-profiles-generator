from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy, QHBoxLayout
from PyQt5.QtGui import QPixmap, QIcon

from src.pages.add_profile_page import AddProfilePage
from src.pages.data_holder import PagesHolder
from src.util.file_util import load_stylesheet
from src.util.sys_util import close_app


class SideMenu(QWidget):
    __stylesheet = "side_menu.qss"

    def __init__(self, add_profile_page: AddProfilePage):
        super().__init__()
        self.add_profile_page = add_profile_page
        self.content_area = PagesHolder().get_content_area()
        self.setObjectName("side_menu_container")
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setContentsMargins(10, 10, 10, 10)
        self.menu_layout.setSpacing(10)
        self.buttons = {}

        self.profiles_button = self.__create_menu_btn("Profiles", "icons/overview.png", 0)
        self.add_profile_button = self.__create_menu_btn("+ Profile", "icons/profiles.png", 1)
        self.menu_button3 = self.__create_menu_btn("Syntax Editor", "icons/editor.png", 2)
        self.logs_button = self.__create_menu_btn("Logs", "icons/logs.png", 3)
        self.settings_button = self.__create_menu_btn("Settings", "icons/settings.png", 4)

        self.menu_layout.addWidget(self.profiles_button)
        self.menu_layout.addWidget(self.add_profile_button)
        self.menu_layout.addWidget(self.menu_button3)
        self.menu_layout.addWidget(self.logs_button)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.menu_layout.addItem(spacer)

        self.bottom_buttons = QFrame()
        self.bottom_layout = QVBoxLayout(self.bottom_buttons)
        self.bottom_layout.setSpacing(5)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.bottom_layout.addWidget(self.settings_button)
        self.logout_button = self.__create_menu_btn("Exit", "icons/logout.png", 5)
        self.logout_button.clicked.connect(close_app)
        self.bottom_layout.addWidget(self.logout_button)

        self.menu_layout.addWidget(self.bottom_buttons)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setObjectName("line")

        self.menu_widget = QWidget()
        self.menu_widget.setMinimumWidth(150)
        self.menu_widget.setMaximumWidth(250)
        self.menu_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.menu_widget.setLayout(self.menu_layout)

        load_stylesheet(self.__stylesheet, self.menu_widget)

    def __on_menu_button_click(self):
        event = self.sender()

        if self.buttons[event] == 1:
            self.add_profile_page.start_create_profile()

        for button in self.buttons:
            if button != event:
                button.setChecked(False)

        event.setChecked(True)
        self.content_area.setCurrentIndex(event.property("index"))

    def __create_menu_btn(self, name, icon_path, index):
        btn = QPushButton(name)
        btn.setObjectName("menu-btn")
        btn.setCheckable(True)
        btn.setProperty("index", index)
        btn.setIcon(QIcon(icon_path))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIconSize(btn.sizeHint())
        btn.clicked.connect(self.__on_menu_button_click)
        self.buttons[btn] = index
        return btn