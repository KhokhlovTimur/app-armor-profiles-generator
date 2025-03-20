from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame, \
    QSpacerItem, QSizePolicy

from src.utils.file_util import load_stylesheet


class SideMenu(QWidget):
    __stylesheet = "side_menu.qss"

    def __init__(self):
        super().__init__()
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setObjectName("side_menu_layout")
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(10)
        self.buttons = {}

        self.profiles_button = self.__create_menu_btn("Profiles", 0)
        self.profiles_button.setProperty("index", 0)
        # menu_button1.setIcon(QIcon("../icon.png"))
        # menu_button1.setIconSize(menu_button1.sizeHint())

        self.add_profile_button = self.__create_menu_btn("+Profile", 1)
        self.menu_button3 = self.__create_menu_btn("Меню 3", 2)

        self.profiles_button.setCursor(Qt.PointingHandCursor)
        self.add_profile_button.setCursor(Qt.PointingHandCursor)
        self.menu_button3.setCursor(Qt.PointingHandCursor)

        self.menu_layout.addWidget(self.profiles_button)
        self.menu_layout.addWidget(self.add_profile_button)
        self.menu_layout.addWidget(self.menu_button3)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.menu_layout.addItem(spacer)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setObjectName("line")

        self.menu_widget = QWidget()
        self.menu_widget.setLayout(self.menu_layout)

        load_stylesheet(self.__stylesheet, self.menu_widget)

    def resizeEvent(self, event):
        max_menu_width = int(self.width() * 0.15)
        self.menu_widget.setFixedWidth(max_menu_width)
        super().resizeEvent(event)

    def __create_menu_btn(self, name, index):
        btn = QPushButton(name)
        btn.setObjectName("menu-btn")
        btn.setCheckable(True)
        btn.setProperty("index", index)
        btn.setChecked(False)
        self.buttons[btn] = index
        return btn

