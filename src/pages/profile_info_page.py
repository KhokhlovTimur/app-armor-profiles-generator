from datetime import datetime, timedelta
from urllib.request import DataHandler

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QSizePolicy,
    QTextEdit, QScrollArea, QGridLayout, QSpacerItem
)
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal

from src.app_armor.app_armor_manager import AppArmorManager
from src.pages.data_holder import PagesHolder
from src.pages.edit_profile_page import EditProfilePage
from src.util.command_executor_util import run_command
from src.util.file_util import load_stylesheet
from src.util.worker_pool import AppArmorWorker


class ProfileInfoPage(QWidget):
    def __init__(self, profile_data, parent):
        super().__init__()
        self.setWindowTitle("Profile Info")
        self.profile_data = profile_data
        self.content_area = PagesHolder().get_content_area()
        self.app_armor_manager = AppArmorManager()
        self.parent = parent
        self.initUI()

    def initUI(self):
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setContentsMargins(20, 20, 20, 20)
        wrapper_layout.setSpacing(10)

        title_label = QLabel(self.profile_data['name'])
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        wrapper_layout.addWidget(title_label, alignment=Qt.AlignTop)

        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignTop)
        info_frame.setStyleSheet("background: #f5f5f5; border-radius: 10px; padding: 10px;")
        info_layout.setSpacing(5)

        mode_label = QLabel(f"<b>Mode:</b> {self.profile_data['mode']}")
        path_label = QLabel(f"<b>Path:</b> {self.profile_data['path']}")
        mode_label.setStyleSheet("font-size: 14px; color: #333;")
        path_label.setStyleSheet("font-size: 14px; color: #333;")

        info_layout.addWidget(mode_label)
        info_layout.addWidget(path_label)
        wrapper_layout.addWidget(info_frame)

        self.content_display = QScrollArea()
        self.content_display.setWidgetResizable(True)
        self.content_display.setStyleSheet("background: #f8f9fa; border-radius: 8px; padding: 10px;")
        self.content_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_display.setVisible(False)

        self.content_display_inner = QWidget()
        self.content_display_layout = QVBoxLayout(self.content_display_inner)
        self.content_display_layout.setAlignment(Qt.AlignTop)
        self.content_display.setWidget(self.content_display_inner)

        wrapper_layout.addWidget(self.content_display, stretch=1)
        wrapper_layout.addWidget(self.toggle_content("code"))

        # Кнопки снизу
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        self.logs_button = QPushButton("Show Logs")
        self.code_button = QPushButton("Show Code")
        self.edit_button = QPushButton("Edit Code")
        self.back_button = QPushButton("Back")

        for button in [self.logs_button, self.code_button, self.edit_button, self.back_button]:
            button.setCursor(Qt.PointingHandCursor)
            load_stylesheet("buttons.qss", button)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.back_button.clicked.connect(self.go_back)
        self.code_button.clicked.connect(lambda: self.toggle_content("code"))
        self.edit_button.clicked.connect(lambda: self.toggle_content("edit"))
        self.logs_button.clicked.connect(lambda: self.toggle_content("logs"))

        button_layout.addWidget(self.logs_button)
        button_layout.addWidget(self.code_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.back_button)

        wrapper_layout.addWidget(button_container)

        self.setLayout(wrapper_layout)

    def toggle_content(self, content_type):
        self.content_display_layout.setAlignment(Qt.AlignTop)

        for i in reversed(range(self.content_display_layout.count())):
            widget = self.content_display_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if content_type == "code":
            code_label = QLabel(self.get_profile_code())
            code_label.setWordWrap(False)
            code_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            code_label.setStyleSheet("""
                font-family: monospace;
                font-size: 13px;
                background-color: white;
                padding: 5px;
            """)
            code_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)

            scroll_container = QWidget()
            scroll_layout = QVBoxLayout(scroll_container)
            scroll_layout.setContentsMargins(0, 0, 0, 0)
            scroll_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            scroll_layout.addWidget(code_label)

            scroll_area.setWidget(scroll_container)
            self.content_display_layout.addWidget(scroll_area)

        elif content_type == "edit":
            self.edit_profile_code()


        elif content_type == "logs":

            logs_label = QLabel("Logs:")

            logs_label.setStyleSheet("font-size: 14px; font-weight: bold;")

            self.scroll_area_logs = QScrollArea()

            self.scroll_area_logs.setWidgetResizable(True)

            self.logs_content_widget = QWidget()

            self.logs_layout = QVBoxLayout(self.logs_content_widget)

            self.logs_layout.setAlignment(Qt.AlignTop)

            self.scroll_area_logs.setWidget(self.logs_content_widget)

            self.content_display_layout.addWidget(logs_label)

            self.content_display_layout.addWidget(self.scroll_area_logs)

            self.load_logs_async()
        elif content_type == "empty":
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            logs_content_layout = QVBoxLayout(scroll_content)
            logs_content_layout.setAlignment(Qt.AlignTop)

        self.content_display.setVisible(True)

    def get_profile_code(self):
        return self.app_armor_manager.read_apparmor_profile_by_name(self.profile_data['name'])

    def edit_profile_code(self):
        edit = EditProfilePage(self.profile_data, self)
        PagesHolder().get_content_area().addWidget(edit)
        PagesHolder().get_content_area().setCurrentWidget(edit)

    def load_logs_async(self):
        self.thread = QThread()
        self.worker = LogWorker(self.profile_data['name'])
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.display_logs)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def go_back(self):
        self.content_area.setCurrentWidget(self.parent)
        self.content_area.removeWidget(self)
        self.deleteLater()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()

    def display_logs(self, logs):
        for log in logs:
            log_label = QLabel(log)
            log_label.setStyleSheet("font-size: 12px; padding: 5px; background: white; border-radius: 5px;")
            self.logs_layout.addWidget(log_label)


class LogWorker(QObject):
    finished = pyqtSignal(list)

    def __init__(self, profile_name):
        super().__init__()
        self.profile_name = profile_name

    def run(self):
        since_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        result = run_command([
            "journalctl", "-q", "--no-pager",
            "--since", since_time,
            "--grep", self.profile_name
        ])
        if result.returncode != 0:
            self.finished.emit(["Ошибка при получении логов"])
        else:
            logs = result.stdout.strip().splitlines()
            self.finished.emit(logs if logs else ["Логи не найдены"])