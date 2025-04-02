import json
import os

from PyQt5 import QtWidgets, QtCore

from src.pages.page_holder import PagesHolder
from src.pages.side_menu import SideMenu
from src.util.file_util import join_project_root


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

    def add_binary(self, parent, path, source):
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
        if hasattr(self, "banner") and self.banner:
            self.banner.deleteLater()

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
        self.banner.raise_()

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

        self.banner.mousePressEvent = lambda event: self._open_new_binaries_page()

        layout.addWidget(icon)
        layout.addWidget(text)
        layout.addStretch()

        self.banner.show()
        QtCore.QTimer.singleShot(60000, self.banner.close)

    def open_profile_creator(self, binary_path):
        if hasattr(self, 'banner'):
            self.banner.close()

    def _open_new_binaries_page(self):
        menu = SideMenu.instance()
        menu.new_binaries_button.animateClick(100)
        self.banner.deleteLater()
        PagesHolder().get_content_area().setCurrentIndex(3)


class NewBinariesPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
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
            create_btn.clicked.connect(lambda _, path=binary["path"]: self.create_profile(path))
            self.table.setCellWidget(row, 2, create_btn)

    def create_profile(self, path):
        # window = ProfileCollectorPage(path)
        # window.show()
        # window.raise_()
        print("123")
