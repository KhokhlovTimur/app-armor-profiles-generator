from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QFrame, QVBoxLayout, QScrollArea, QLineEdit
from PyQt5.QtCore import Qt

from src.app_armor.app_armor_manager import AppArmorManager
from src.utils.file_util import load_stylesheet


class ProfilesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.content_layout = None
        self.all_items = []  # Хранение всех профилей для поиска
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Поиск по названию или пути...")
        self.search_input.textChanged.connect(self.filter_profiles)
        main_layout.addWidget(self.search_input)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        load_stylesheet("scrollbar.qss", self.scroll_area)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)

        self.all_items = self.__get_profiles()

        if not self.all_items:
            no_data_label = QLabel("No profiles found or failed to retrieve data.")
            self.content_layout.addWidget(no_data_label, 0, 0)
        else:
            self.display_profiles(self.__get_profiles())

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        self.content_layout.setRowStretch(len(self.all_items), 1)
        self.setLayout(main_layout)
        self.setWindowTitle('Profiles')

    def display_profiles(self, profiles: None):
        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().deleteLater()

        if profiles is None:
            profiles = self.__get_profiles()

        for index, profile in enumerate(profiles):
            self.create_item(profile, row=index, col=0)

    def __get_profiles(self):
        self.all_items = AppArmorManager().get_profiles_data()
        return self.all_items

    def create_item(self, profile_data, row, col):
        container = QFrame()
        container.setMinimumSize(300, 170)
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid black;
                padding: 15px;
            }
            QLabel {
                font-size: 14px;
                color: #333;
                border: none;
                background: transparent;
            }
        """)
        container_layout = QGridLayout(container)

        title_label = QLabel(f"<b>{profile_data['name']}</b>")
        mode_label = QLabel(f"Mode: {profile_data['mode']}")
        path_label = QLabel(f"Path: {profile_data['path']}")

        title_label.setWordWrap(True)
        mode_label.setWordWrap(True)
        path_label.setWordWrap(True)

        container_layout.addWidget(title_label, 0, 0)
        container_layout.addWidget(mode_label, 1, 0)
        container_layout.addWidget(path_label, 2, 0)

        self.content_layout.addWidget(container, row, col)

    def filter_profiles(self):
        search_text = self.search_input.text().lower()
        filtered_profiles = [
            profile for profile in self.all_items
            if search_text in profile['name'].lower() or search_text in profile['path'].lower()
        ]
        self.display_profiles(filtered_profiles)
