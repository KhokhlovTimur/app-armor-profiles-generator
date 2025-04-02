from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy, QHBoxLayout, \
    QStackedWidget
from PyQt5.QtGui import QPixmap, QIcon

from src.pages.add_profile import AddProfilePage
from src.pages.generator_pages_stack import StartGenerateProfilePage
from src.pages.page_holder import PagesHolder
from src.pages.generate_profile_items_stack import ProfileManager,  LogMonitorPage, ProfileDiffPage
from src.util.file_util import load_stylesheet, join_project_root
from src.util.sys_util import close_app


class SideMenu(QWidget):
    _instance = None
    __stylesheet = "side_menu.qss"

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.add_profile_page = AddProfilePage.instance()
        self.content_area = PagesHolder().get_content_area()
        self.setObjectName("side_menu_container")
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setContentsMargins(10, 10, 10, 10)
        self.menu_layout.setSpacing(10)
        self.buttons = {}

        self.status_button = self.__create_menu_btn("Status", join_project_root("resources", "icons", "1status.png"), 0)
        self.profiles_button = self.__create_menu_btn("Profiles", join_project_root("resources", "icons", "1profiles.png"), 1)
        self.add_profile_button = self.__create_menu_btn("Create Profile", join_project_root("resources", "icons", "1add_profile.png"), 2)
        self.new_binaries_button = self.__create_menu_btn("New Binaries", join_project_root("resources", "icons", "1binaries.png"), 3)
        self.generate_button = self.__create_menu_btn("Generate Profile", "icons/logs.png", 4)
        self.about_button = self.__create_menu_btn("About", "icons/settings.png", 5)
        self.settings_button = self.__create_menu_btn("Settings", "icons/settings.png", 6)

        self.menu_layout.addWidget(self.status_button)
        self.menu_layout.addWidget(self.profiles_button)
        self.menu_layout.addWidget(self.add_profile_button)
        self.menu_layout.addWidget(self.new_binaries_button)
        self.menu_layout.addWidget(self.generate_button)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.menu_layout.addItem(spacer)

        self.bottom_buttons = QFrame()
        self.bottom_layout = QVBoxLayout(self.bottom_buttons)
        self.bottom_layout.setSpacing(5)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.bottom_layout.addWidget(self.about_button)
        self.bottom_layout.addWidget(self.settings_button)
        self.logout_button = self.__create_menu_btn("Exit", "icons/logout.png", 7)
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

        if self.buttons[event] == 2:
            self.add_profile_page.start_create_profile()

        # if self.buttons[event] == 4:
            # self.stack = StartGenerateProfilePage().init_stack()

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
        icon = QIcon(icon_path)
        btn.setIcon(icon)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIconSize(QSize(24, 24))
        btn.clicked.connect(self.__on_menu_button_click)
        self.buttons[btn] = index
        return btn