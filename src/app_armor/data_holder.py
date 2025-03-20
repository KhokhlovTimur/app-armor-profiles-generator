from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QPalette, QColor
import sys
import subprocess

class DataHolder:
    _instance = None
    # __pswd = None
    __pswd = open('../../creds/pswd.txt').readline()

    def get_pswd(self):
        return DataHolder.__pswd

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataHolder, cls).__new__(cls, *args, **kwargs)
        DataHolder.__pswd = cls.__request_password()
        return cls._instance

    @staticmethod
    def __request_password():
        if DataHolder.__pswd is not None:
            return DataHolder.__pswd
        while True:
            password, ok = QInputDialog.getText(None, "Enter sudo password", "Password:", QLineEdit.Password)
            if not ok or not password:
                print("Пароль не был введён. Завершение.")
                sys.exit(1)

            # Проверка пароля
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
                # Сообщение об ошибке
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setText("Incorrect password. Try again.")
                msg_box.setWindowTitle("Error")
                msg_box.exec_()