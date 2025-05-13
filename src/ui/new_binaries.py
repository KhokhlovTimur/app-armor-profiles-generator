import json
import os

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QPropertyAnimation
from PyQt5.QtWidgets import QGraphicsOpacityEffect

from src.ui.create_profile.profile_create_start import StartGenerateProfilePage
from src.ui.page_holder import PagesHolder
from src.ui.side_menu import SideMenu
from src.util.file_util import join_project_root, load_stylesheet_buttons


class NewBinariesHandler:
    _instance = None
    STORAGE_PATH = join_project_root("data", "new_binaries.txt")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NewBinariesHandler, cls).__new__(cls)
            cls._instance.new_binaries = []
            if not os.path.exists(cls._instance.STORAGE_PATH):
                with open(cls._instance.STORAGE_PATH, "w") as f:
                    pass

        return cls._instance

    def add_binary(self, parent, start_generate_page: StartGenerateProfilePage, path, source):
        self.start_generate_page = start_generate_page
        self.parent = parent
        binary = {'path': path, 'source': source}
        self.show_binary_notification(path, source)
        if binary not in self.new_binaries:
            self.new_binaries.append(binary)
            self.append_binary_to_file(binary)
            self.show_binary_notification(path, source)

    def get_binaries(self):
        if os.path.exists(NewBinariesHandler.STORAGE_PATH):
            try:
                with open(NewBinariesHandler.STORAGE_PATH, "r") as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                print(f"{e}")
                return []
        else:
            return []

    def append_binary_to_file(self, entry):
        data = []

        if os.path.exists(self.STORAGE_PATH):
            try:
                with open(self.STORAGE_PATH, "r") as f:
                    data = json.load(f)
            except Exception:
                data = []

        if entry not in data:
            data.append(entry)
            try:
                os.makedirs(os.path.dirname(self.STORAGE_PATH), exist_ok=True)
                with open(self.STORAGE_PATH, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Ошибка при записи: {e}")

    def remove_binaries(self, path_to_remove):
        if not os.path.exists(self.STORAGE_PATH):
            return

        try:
            with open(self.STORAGE_PATH, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"{e}")
            return

        updated_data = [item for item in data if item.get("path") != path_to_remove]

        try:
            with open(self.STORAGE_PATH, "w") as f:
                json.dump(updated_data, f, indent=2)
            print(f"Deleted : {path_to_remove}")
        except Exception as e:
            print(f"{e}")

    def show_binary_notification(self, path, source):
        if hasattr(self, "banner") and self.banner and not self._banner_closing:
            self._close_banner(force=True)

        self._banner_closing = False

        self.banner = QtWidgets.QWidget(self.parent)
        self.banner.setFixedSize(320, 80)
        self.banner.setStyleSheet("""
            background-color: #d6f5e9;
            border-radius: 8px;
        """)

        margin = 12
        self.banner.move(self.parent.width() - self.banner.width() - margin, margin)
        self.banner.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.banner.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.banner.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.banner.setFocusPolicy(QtCore.Qt.NoFocus)

        layout = QtWidgets.QHBoxLayout(self.banner)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        icon = QtWidgets.QLabel()
        icon.setPixmap(self.parent.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation).pixmap(24, 24))

        text = QtWidgets.QLabel(f"<div style='font-size:13px;'>"
                                f"<b>New binary:</b> {path}<br>"
                                f"<span style='color:gray;'>Source: {source}</span></div>")
        text.setStyleSheet("border: none;")
        text.setTextFormat(QtCore.Qt.RichText)

        layout.addWidget(icon)
        layout.addWidget(text)
        layout.addStretch()

        self.banner.mousePressEvent = lambda event: self._on_click_notification(path)

        self.effect = QGraphicsOpacityEffect(self.banner)
        self.banner.setGraphicsEffect(self.effect)

        self.fade_anim = QPropertyAnimation(self.effect, b"opacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

        self.banner.show()

        QtCore.QTimer.singleShot(8000, self._close_banner)

    def open_profile_creator(self, binary_path):
        if hasattr(self, 'banner'):
            self._close_banner()

    def _on_click_notification(self, path):
        self._close_banner()
        self.start_generate_page.select_page.set_binary_path(path)
        PagesHolder().get_content_area().setCurrentWidget(self.start_generate_page.stack)

    def _close_banner(self, force=False):
        if hasattr(self, "banner") and self.banner:
            if force:
                self.banner.close()
                self.banner = None
                return

            self._banner_closing = True

            self.fade_out = QPropertyAnimation(self.banner.graphicsEffect(), b"opacity")
            self.fade_out.setDuration(300)
            self.fade_out.setStartValue(1.0)
            self.fade_out.setEndValue(0.0)
            self.fade_out.finished.connect(self._finalize_close)
            self.fade_out.start()

    def _finalize_close(self):
        if hasattr(self, "banner") and self.banner:
            self.banner.close()
            self.banner = None
            self._banner_closing = False


class NewBinariesPage(QtWidgets.QWidget):
    def __init__(self, start_generate_page: StartGenerateProfilePage):
        super().__init__()
        self.start_generate_page = start_generate_page
        self.setWindowTitle("Новые бинарники")
        self.setMinimumSize(600, 400)

        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Путь", "Источник", "Действие"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh_button = QtWidgets.QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.populate)
        layout.addWidget(self.refresh_button, alignment=QtCore.Qt.AlignRight)

        self.populate()

    def populate(self):
        handler = NewBinariesHandler()
        binaries = handler.get_binaries()

        self.table.setRowCount(0)
        for binary in binaries:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(binary["path"]))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(binary["source"]))

            create_btn = QtWidgets.QPushButton("Создать профиль")
            load_stylesheet_buttons(create_btn)
            create_btn.clicked.connect(lambda _, path=binary["path"]: self.create_profile(path))
            self.table.setCellWidget(row, 2, create_btn)

    def create_profile(self, path):
        self.start_generate_page.select_page.set_binary_path(path)
        PagesHolder().get_content_area().setCurrentWidget(self.start_generate_page.stack)
