from PyQt5.QtCore import pyqtSignal, QObject


class ExecutablePage(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
