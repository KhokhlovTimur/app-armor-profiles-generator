import re
import subprocess

from PyQt5 import QtWidgets, QtCore

from src.util.command_executor_util import run_command
from src.util.file_util import load_stylesheet


class AppArmorStatusPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AppArmor Status")
        load_stylesheet("apparmor_status", self)
        self.create_widgets()
        self.create_layout()
        self.refresh_status()

    def create_widgets(self):
        self.status_label = QtWidgets.QLabel("Loading status...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        self.text_output = QtWidgets.QPlainTextEdit()
        self.text_output.setReadOnly(True)

        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.start_button = QtWidgets.QPushButton("Enable AppArmor")
        self.stop_button = QtWidgets.QPushButton("Disable AppArmor")
        self.restart_button = QtWidgets.QPushButton("Reload AppArmor")

        self.refresh_button.clicked.connect(self.refresh_status)
        self.start_button.clicked.connect(lambda: self.control_service("start"))
        self.stop_button.clicked.connect(lambda: self.control_service("stop"))
        self.restart_button.clicked.connect(lambda: self.control_service("reload"))

    def create_layout(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_output)

        button_wrapper = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_wrapper)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.restart_button)

        load_stylesheet("buttons.qss", button_wrapper)
        layout.addWidget(button_wrapper)

        layout.addLayout(button_layout)

    def refresh_status(self):
        output_lines = []

        try:
            full_status = run_command(["sudo", "-S", "systemctl", "status", "apparmor"]).stdout

            header_part = full_status.split("\n")
            cut_index = 0
            for i, line in enumerate(header_part):
                if re.match(r"^\w{3} \d{1,2} \d{2}:\d{2}:\d{2}", line):
                    cut_index = i
                    break
            trimmed_status = "\n".join(header_part[:cut_index]) if cut_index else full_status

            output_lines.append("[ systemctl status apparmor ]")
            output_lines.append(trimmed_status.strip())

            systemctl_status = run_command(["sudo", "-S", "systemctl", "is-active", "apparmor"]).stdout.strip()
            if systemctl_status == "active":
                self.status_label.setText("AppArmor: <font color='green'>Active</font>")
            elif systemctl_status == "inactive":
                self.status_label.setText("AppArmor: <font color='red'>Inactive</font>")
            else:
                self.status_label.setText(f"AppArmor: ⚠️ <font color='orange'>{systemctl_status}</font>")
        except Exception as e:
            self.status_label.setText(f"AppArmor: ⚠️ <font color='gray'>Error ({e})</font>")
            output_lines.append(f"Error parsing systemctl: {e}")

        self.text_output.setPlainText("\n".join(output_lines))

    def control_service(self, action):
        try:
            run_command(["sudo", "-S", "systemctl", action, "apparmor"])
            self.refresh_status()
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"{e}")
