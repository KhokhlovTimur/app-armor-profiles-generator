import subprocess
import sys

from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton


class CredentialsHolder:
    _instance = None
    # __pswd = None
    __pswd = open('../../creds/pswd.txt').readline()

    def get_pswd(self):
        return CredentialsHolder.__pswd

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CredentialsHolder, cls).__new__(cls, *args, **kwargs)
        CredentialsHolder.__pswd = cls.__request_password()
        return cls._instance

    @staticmethod
    def __request_password():
        if CredentialsHolder.__pswd is not None:
            return CredentialsHolder.__pswd
        while True:
            dialog = PasswordDialog()
            password, ok = dialog.get_password()
            if not ok or not password:
                print("Пароль не был введён. Завершение.")
                sys.exit(1)

            result = subprocess.run(
                ['sudo', '-S', 'echo', 'password check'],
                input=password + '\n',
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("Пароль успешно проверен.")
                return password
            else:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setText("Incorrect password. Try again.")
                msg_box.setWindowTitle("Error")
                msg_box.exec_()

class PasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudo password")
        self.setMinimumWidth(400)

        self.password = None

        layout = QVBoxLayout()

        label = QLabel("Password:")
        label.setStyleSheet("font-size: 16px;")
        layout.addWidget(label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("font-size: 16px; padding: 6px;")
        layout.addWidget(self.password_input)

        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet("font-size: 14px; padding: 6px;")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def get_password(self):
        if self.exec_() == QDialog.Accepted:
            return self.password_input.text(), True
        return "", False