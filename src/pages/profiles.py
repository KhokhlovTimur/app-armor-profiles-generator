from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QLineEdit,
    QGridLayout, QHBoxLayout, QSizePolicy, QSpacerItem, QComboBox, QStackedWidget
)
from PyQt5.QtCore import Qt

from src.app_armor.apparmor_manager import AppArmorManager
from src.pages.page_holder import PagesHolder
from src.pages.profile_info import ProfileInfoPage
from src.util.file_util import load_stylesheet


class ProfilesPage(QWidget):
    __styles = "profiles_page.qss"
    ITEMS_PER_PAGE = 5

    def __init__(self):
        super().__init__()
        self.content_layout = None
        self.all_items = []
        self.content_area = PagesHolder().get_content_area()
        self.current_page = 0
        self.filtered_profiles = []
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("AppArmor Profiles - Overview")
        title_label.setObjectName("page_title")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding-bottom: 10px;")
        main_layout.addWidget(title_label)

        control_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search")
        self.search_input.textChanged.connect(self.filter_profiles)
        control_layout.addWidget(self.search_input)
        main_layout.addLayout(control_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        load_stylesheet("scrollbar.qss", self.scroll_area)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        load_stylesheet(ProfilesPage.__styles, self.content_widget)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

        self.pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.page_label = QLabel()
        self.page_selector = QComboBox()
        self.page_selector.currentIndexChanged.connect(self.select_page)

        self.pagination_layout.addWidget(self.prev_button)
        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.page_selector)
        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.next_button)

        self.pagination_container = QWidget()
        self.pagination_container.setLayout(self.pagination_layout)
        main_layout.addWidget(self.pagination_container)

        self.setLayout(main_layout)
        self.all_items = self.__get_profiles()
        self.filtered_profiles = self.all_items
        self.update_pagination()

    def display_profiles(self):
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        start = self.current_page * self.ITEMS_PER_PAGE
        end = start + self.ITEMS_PER_PAGE
        profiles = self.filtered_profiles[start:end]

        for index, profile in enumerate(profiles):
            self.create_profile_card(profile, row=index, col=0)

        self.content_widget.setMinimumHeight(self.ITEMS_PER_PAGE * 130)

    def update_pagination(self):
        total_pages = max(1, (len(self.filtered_profiles) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled((self.current_page + 1) * self.ITEMS_PER_PAGE < len(self.filtered_profiles))

        self.page_selector.blockSignals(True)
        self.page_selector.clear()
        self.page_selector.addItems([str(i + 1) for i in range(total_pages)])
        self.page_selector.setCurrentIndex(self.current_page)
        self.page_selector.blockSignals(False)

        self.display_profiles()

    def next_page(self):
        if (self.current_page + 1) * self.ITEMS_PER_PAGE < len(self.filtered_profiles):
            self.current_page += 1
            self.update_pagination()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_pagination()

    def select_page(self, index):
        self.current_page = index
        self.update_pagination()

    def filter_profiles(self):
        search_text = self.search_input.text().lower()
        self.filtered_profiles = [
            profile for profile in self.__get_profiles()
            if search_text in profile['name'].lower() or search_text in profile['path'].lower()
        ]
        self.current_page = 0
        self.update_pagination()

    def __get_profiles(self):
        return AppArmorManager().get_profiles_from_apparmor_d()

    def create_profile_card(self, profile_data, row, col):
        container = QFrame()
        container.setObjectName("profile_card")
        container.setMinimumSize(300, 120)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        container.setMaximumHeight(170)
        container_layout = QGridLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel(f"<b>{profile_data['name']}</b>")
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 16px; color: black; background: transparent;")

        description_label = QLabel("Profile from /etc/apparmor.d")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 12px; color: gray; background: transparent;")

        container_layout.addWidget(title_label, 0, 0)
        container_layout.addWidget(description_label, 1, 0)

        info_layout = QVBoxLayout()
        # mode_label = QLabel(f"Mode: {profile_data['mode']}")
        # path_label = QLabel(f"Path: {profile_data['path']}")
        # mode_label.setStyleSheet("font-size: 12px; color: black; background: transparent;")
        # path_label.setStyleSheet("font-size: 12px; color: black; background: transparent;")
        # info_layout.addWidget(mode_label)
        # info_layout.addWidget(path_label)

        container_layout.addLayout(info_layout, 0, 1)

        details_button = QPushButton("Details")
        details_button.setObjectName("details_btn")
        details_button.setCursor(Qt.PointingHandCursor)
        details_button.clicked.connect(lambda: self.__open_profile(profile_data))
        container_layout.addWidget(details_button, 0, 2, Qt.AlignRight)

        self.content_layout.addWidget(container, row, col)

    def __open_profile(self, profile_data):
        profile = ProfileInfoPage(profile_data, self)
        self.content_area.addWidget(profile)
        self.content_area.setCurrentWidget(profile)
