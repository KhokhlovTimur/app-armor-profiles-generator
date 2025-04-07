import shutil
import subprocess
from operator import contains

from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox

from src.apparmor.credentials_holder import CredentialsHolder


def run_command(command):
    try:
        if 'sudo' not in command:
            return subprocess.run(
                command,
                capture_output=True,
                text=True)
        else:
            return subprocess.run(
                command,
                input=f'{CredentialsHolder().get_pswd()}\n',
                capture_output=True,
                text=True)
    except Exception as e:
        return subprocess.CompletedProcess(args=command, returncode=1, stdout='', stderr=str(e))


def launch_command_interactive(cmd, parent, exec_func=None, is_run: bool=True) -> None | QProcess:
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
    done_button.clicked.connect(lambda: (dialog.accept(), exec_func())[1] if exec_func else dialog.accept())
    layout.addWidget(done_button)

    # process.finished.connect(lambda a,b : (done_button.click(), exec_func()))

    terminal = shutil.which("gnome-terminal") or shutil.which("xterm")
    if terminal:
        try:
            new_cmd = f'cd /'
            new_cmd += "; exec bash"

            if "gnome-terminal" in terminal:
                process.start(terminal, ["--", "bash", "-c", new_cmd])
            elif "xterm" in terminal:
                process.start(terminal, ["-e", f"bash -c \"{new_cmd}\""])
        except Exception as e:
            QMessageBox.critical(parent, "Ошибка запуска", str(e))
            return None
    else:
        QMessageBox.critical(parent, "Ошибка", "Не найден поддерживаемый терминал.")
        return None

    dialog.exec_()

    return process
