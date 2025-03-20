from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QFrame, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt

from src.app_armor.command_executor import AppArmorManager


class ProfilesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.content_layout = None
        self.initUI()

    def initUI(self):
        # Создаем основной layout для окна
        main_layout = QVBoxLayout(self)

        # Создаем QScrollArea для прокрутки
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        scroll_area.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: black;
                border-radius: 6px;
                min-height: 20px;
            }
        """)

        # Вложенный виджет, куда будут помещаться все элементы
        content_widget = QWidget()
        self.content_layout = QGridLayout(content_widget)

        # Получаем данные профилей
        self.items = AppArmorManager().get_profiles_data()

        if not self.items:
            no_data_label = QLabel("No profiles found or failed to retrieve data.")
            self.content_layout.addWidget(no_data_label, 0, 0)
        else:
            self.display_profiles()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.content_layout.setRowStretch(len(self.items), 1)
        self.setLayout(main_layout)
        self.setWindowTitle('Profiles')
        self.resize(600, 400)

    def display_profiles(self):
        for index, profile in enumerate(self.items):
            self.create_item(profile, row=index, col=0)

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
                border: none; /* Убираем обводку текста */
                background: transparent; /* Прозрачный фон для текста */
            }
        """)
        container_layout = QGridLayout(container)

        # Profile Info
        title_label = QLabel(f"<b>{profile_data['name']}</b>")
        mode_label = QLabel(f"Mode: {profile_data['mode']}")
        path_label = QLabel(f"Path: {profile_data['path']}")

        # Включаем перенос текста
        title_label.setWordWrap(True)
        mode_label.setWordWrap(True)
        path_label.setWordWrap(True)

        # Добавляем элементы в контейнер
        container_layout.addWidget(title_label, 0, 0)
        container_layout.addWidget(mode_label, 1, 0)
        container_layout.addWidget(path_label, 2, 0)

        self.content_layout.addWidget(container, row, col)

