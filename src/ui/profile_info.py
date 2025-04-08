from PyQt5 import sip
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QSizePolicy,
    QScrollArea, QComboBox, QTableWidgetItem, QHeaderView, QTableWidget
)

from src.apparmor.apparmor_manager import get_profile_mode_by_name, change_profile_mode, get_logs_not_empty, \
    read_apparmor_profile_by_name
from src.model.apparmor_profile import AppArmorProfile
from src.ui.profile_edit import EditProfilePage
from src.ui.page_holder import PagesHolder
from src.util.apparmor_util import parse_profile_rules, extract_profile_path
from src.util.file_util import load_stylesheet


class ProfileInfoPage(QWidget):
    def __init__(self, profile_data, parent):
        super().__init__()
        self.setWindowTitle("Profile Info")
        self.content_area = PagesHolder().get_content_area()
        self.profile = AppArmorProfile(name=profile_data['name'], path=extract_profile_path(read_apparmor_profile_by_name(profile_data['name'])), disabled=profile_data['disabled'], mode=profile_data['mode'])
        self.parent = parent
        self.initUI()

    def initUI(self):
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setContentsMargins(20, 20, 20, 20)
        wrapper_layout.setSpacing(10)

        title_bar = QHBoxLayout()
        title_bar.setAlignment(Qt.AlignLeft)

        title_label = QLabel(self.profile.name)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        title_bar.addWidget(title_label)
        title_bar.addStretch()

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["enforce", "complain"])
        self.mode_selector.setVisible(False)
        self.mode_selector.setStyleSheet("""
            QComboBox {
                padding: 5px;
                font-size: 13px;
                border-radius: 5px;
                border: 1px solid #ccc;
                background-color: white;
            }
            QComboBox::drop-down {
                width: 20px;
            }
        """)

        self.apply_mode_btn = QPushButton("Apply")
        self.apply_mode_btn.setObjectName("top_btn")
        self.apply_mode_btn.setVisible(False)
        self.apply_mode_btn.clicked.connect(self.apply_mode_change)

        self.cancel_mode_btn = QPushButton("Cancel")
        self.cancel_mode_btn.setObjectName("top_btn")
        self.cancel_mode_btn.setVisible(False)
        self.cancel_mode_btn.clicked.connect(self.cancel_mode_change)

        self.change_mode_btn = QPushButton("Change Mode")
        self.change_mode_btn.setObjectName("top_btn")
        self.change_mode_btn.clicked.connect(self.show_mode_selector)

        self.disable_btn = QPushButton("Enable Profile" if self.profile.disabled else "Disable Profile")
        self.disable_btn.setObjectName("top_btn")
        self.disable_btn.clicked.connect(self.disable_or_enable_profile)

        for btn in [self.mode_selector, self.apply_mode_btn, self.cancel_mode_btn, self.change_mode_btn,
                    self.disable_btn]:
            load_stylesheet("buttons.qss", btn)
            title_bar.addWidget(btn)

        wrapper_layout.addLayout(title_bar)

        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_left = QVBoxLayout()
        info_left.setAlignment(Qt.AlignTop)

        mode_label = QLabel(f"<b>Mode:</b> {self.profile.mode}")
        self.mode_label = mode_label
        path_label = QLabel(f"<b>Path:</b> {self.profile.path}")

        mode_label.setStyleSheet("font-size: 14px; color: #333;")
        path_label.setStyleSheet("font-size: 14px; color: #333;")

        info_left.addWidget(mode_label)
        info_left.addWidget(path_label)
        info_layout.addLayout(info_left)

        wrapper_layout.addWidget(info_frame)

        self.view_mode_selector = QComboBox()
        self.view_mode_selector.addItems(["Code View", "Table View"])
        self.view_mode_selector.setFixedWidth(150)
        self.view_mode_selector.currentIndexChanged.connect(self.on_view_mode_changed)
        load_stylesheet("combobox.qss", self.view_mode_selector)

        view_selector_widget = QWidget()
        view_selector_layout = QHBoxLayout(view_selector_widget)
        view_selector_layout.setContentsMargins(0, 0, 10, 0)
        view_selector_layout.setAlignment(Qt.AlignRight)
        view_selector_layout.addWidget(self.view_mode_selector)
        wrapper_layout.addWidget(view_selector_widget)

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
        if self.profile.disabled:
            self.edit_button.hide()
        button_layout.addWidget(self.back_button)

        wrapper_layout.addWidget(button_container)

        self.setLayout(wrapper_layout)

    def on_view_mode_changed(self, index):
        if index == 0:
            self.toggle_content("code")
        elif index == 1:
            self.toggle_content("table")

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

        elif content_type == "table":
            self.show_table_view()

        elif content_type == "empty":
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            logs_content_layout = QVBoxLayout(scroll_content)
            logs_content_layout.setAlignment(Qt.AlignTop)

        self.content_display.setVisible(True)

    def show_table_view(self):
        code = self.get_profile_code()
        parsed = parse_profile_rules(code)

        table = QTableWidget()
        table.verticalHeader().setVisible(False)
        table.setCornerButtonEnabled(False)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Path / Rule", "Permissions"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet("font-family: monospace; font-size: 12px;  margin-top: 10px")

        row = 0

        for inc in parsed:
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(inc))
            table.setItem(row, 1, QTableWidgetItem(""))
            row += 1

        self.content_display_layout.addWidget(table)

    def get_profile_code(self):
        return read_apparmor_profile_by_name(self.profile.name)

    def edit_profile_code(self):
        edit = EditProfilePage(self.profile, self)
        PagesHolder().get_content_area().addWidget(edit)
        PagesHolder().get_content_area().setCurrentWidget(edit)

    def load_logs_async(self):
        # future = AppArmorWorker().run_async(
        #     lambda: self.app_armor_manager.get_logs_not_empty(self.profile.name, None)
        # )
        # self.watcher = TaskWatcher(future)
        # self.watcher.finished.connect(lambda f: self.display_logs(f))
        self.display_logs(get_logs_not_empty(self.profile.name, extract_profile_path(read_apparmor_profile_by_name(self.profile.name)), None))

    def go_back(self):
        self.content_area.setCurrentWidget(self.parent)
        self.content_area.removeWidget(self)
        self.deleteLater()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()

    def display_logs(self, logs: list[str]):
        if self.logs_layout is None or sip.isdeleted(self.logs_layout):
            return

        for log in logs:
            log_label = QLabel()
            log_label.setWordWrap(True)
            log_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

            bg_color = "#ffffff"
            if "DENIED" in log:
                bg_color = "#ffe6e6"
            elif "profile_replace" in log:
                bg_color = "#f2f2f2"
            elif "profile_remove" in log:
                bg_color = "#fff2cc"
            elif "ERROR" in log or "fail" in log.lower():
                bg_color = "#ffcccc"

            log_label.setStyleSheet(f"""
                background-color: {bg_color};
                font-family: monospace;
                font-size: 12px;
                padding: 8px;
                border-radius: 6px;
                margin-bottom: 4px;
            """)

            log_label.setText(log.strip())
            self.logs_layout.addWidget(log_label)

        self.scroll_area_logs.setStyleSheet("""
            QScrollBar:vertical {
                background: #e0e0e0;
                width: 10px;
                margin: 2px 0;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: black;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #666666;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

    def show_mode_selector(self):
        self.mode_selector.setVisible(True)
        self.apply_mode_btn.setVisible(True)
        self.cancel_mode_btn.setVisible(True)
        self.change_mode_btn.setVisible(False)

    def cancel_mode_change(self):
        self.mode_selector.setVisible(False)
        self.apply_mode_btn.setVisible(False)
        self.cancel_mode_btn.setVisible(False)
        self.change_mode_btn.setVisible(True)

    def apply_mode_change(self):
        new_mode = self.mode_selector.currentText()
        result = change_profile_mode(self.profile.name, new_mode)

        if result.returncode == 0:
            self.update_profile()
        else:
            print("Error change mode")

        self.profile.mode = get_profile_mode_by_name(self.profile.name)
        self.mode_selector.setVisible(False)
        self.apply_mode_btn.setVisible(False)
        self.cancel_mode_btn.setVisible(False)
        self.change_mode_btn.setVisible(True)

    def disable_or_enable_profile(self):
        mode = 'enable' if self.profile.disabled else 'disable'
        result = change_profile_mode(self.profile.name, mode)

        if result.returncode == 0:
            self.update_profile()
        else:
            print(result.stderr)

    def update_profile(self):
        self.profile.mode = get_profile_mode_by_name(self.profile.name)
        self.mode_label.setText(f"<b>Mode:</b> {self.profile.mode}")
        self.profile.disabled = self.profile.mode == 'disabled'
        self.disable_btn.setText("Enable Profile" if self.profile.disabled else "Disable Profile")
        if self.profile.disabled:
            self.edit_button.hide()
        else:
            self.edit_button.show()
