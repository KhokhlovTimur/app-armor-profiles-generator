import subprocess
import sys

from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox


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
            password, ok = QInputDialog.getText(None, "Enter sudo password", "Password:", QLineEdit.Password)
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