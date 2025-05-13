from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QDialog, \
    QProgressBar, QLabel

from src.util.file_util import join_project_root


class SandboxConsole:
    __script_path = "sandbox_bash.sh"

    def run_script(self, parent, exec_func=None) -> QProcess:
        process = QProcess(parent)

        dialog = QDialog(parent)
        dialog.setWindowTitle("")
        dialog.setModal(True)
        dialog.setFixedSize(360, 140)
        dialog.setWindowFlags(dialog.windowFlags())

        layout = QVBoxLayout(dialog)
        label = QLabel("Use the application.\nClick 'Finish' when you are done.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        progress = QProgressBar()
        progress.setRange(0, 0)
        layout.addWidget(progress)

        done_button = QPushButton("Finish")
        done_button.clicked.connect(lambda: (dialog.accept(), exec_func())[1] if exec_func else (dialog.accept()))
        layout.addWidget(done_button)

        process.start(
            "gnome-terminal",
            [
                "--",
                "bash",
                "-c",
                "bash " + join_project_root("scripts/", self.__script_path) + "; exec bash"
            ]
        )

        dialog.exec_()

        return process

