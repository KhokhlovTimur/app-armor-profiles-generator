import fcntl
import os
import pty
import subprocess
from datetime import datetime
from subprocess import Popen

from PyQt5.QtCore import QSocketNotifier, pyqtSignal, QObject

from src.apparmor.apparmor_parser import validate_and_load_profile
from src.apparmor.credentials_holder import CredentialsHolder
from src.constants import LOGS_TIME_PATTERN
from src.model.apparmor_profile import AppArmorProfile
from src.util.command_executor_util import launch_command_interactive
from src.util.file_util import join_project_root


class ProfileFromLogsGenerator(QObject):
    on_data_received = pyqtSignal(str)
    on_proc_terminated = pyqtSignal()

    tmp_logs_path = join_project_root("data/", "logs")

    def __init__(self):
        super().__init__()
        self.profile = None

    def start_generate(self, bin_path):
        profile = AppArmorProfile(path=bin_path, includes=["abstractions/base"])
        self.profile = profile
        profile_string = profile.render()
        return validate_and_load_profile(profile_string, profile.path)

    def exec_app(self, parent):
        print(f'exec {self.profile.path}')
        self.parent = parent
        self.start_time = datetime.now().strftime(LOGS_TIME_PATTERN)
        launch_command_interactive(f"{self.profile.path}; exec bash", parent, self._analyze_profile_logs)

    def _analyze_profile_logs(self):
        # dialog = QDialog(self.parent)
        # dialog.setWindowTitle("Find logs...")
        # dialog.setModal(True)
        # dialog.setFixedSize(360, 140)
        # dialog.setWindowFlags(dialog.windowFlags())
        #
        # layout = QVBoxLayout(dialog)
        # label = QLabel("Wait")
        # label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(label)
        #
        # progress = QProgressBar()
        # progress.setRange(0, 0)
        # self.parent.layout().addWidget(progress)

        try:
            subprocess.run(
                ["bash", join_project_root("scripts/", "redirect_logs.sh"), self.profile.path, self.start_time, self.tmp_logs_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        finally:
            # dialog.accept()
            pass

    def to_ascii(self, text):
        return text.encode("ascii", errors="ignore").decode("ascii")

    def run_generate(self) -> tuple[Popen[str], int] | None:
        try:
            self.master_fd, slave_fd = pty.openpty()

            env = os.environ.copy()
            env["TERM"] = "dumb"
            env["PAGER"] = "cat"

            self.process = subprocess.Popen(
                ["sudo", "-S", "aa-logprof", "-f", self.tmp_logs_path],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                env=env,
                text=True,
                bufsize=1,
                close_fds=True
            )

            os.close(slave_fd)

            os.write(self.master_fd, (CredentialsHolder().get_pswd() + "\n").encode())

            flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            self.notifier = QSocketNotifier(self.master_fd, QSocketNotifier.Read)
            self.notifier.activated.connect(self.__read_and_push_chunk)

            return self.process, self.master_fd

        except Exception as e:
            print(f"Error in profile {self.profile.path} generating: {e}")

    def __read_and_push_chunk(self):
        try:
            chunk = self.__read_full_chunk()
            if chunk:
                print(chunk)
                self.first_text_received = True
                self.output_buffer = chunk
                if "Press RETURN to continue" in chunk:
                    os.write(self.master_fd, b"\n")
                    return

                self.on_data_received.emit(self.output_buffer)
            else:
                self.notifier.setEnabled(False)
                print(f"Profile {self.profile.path} is ready.")
                self.on_data_received.emit(f"Profile {self.profile.path} is ready.")

            if self.process and self.process.poll() is not None:
                print("Process finished.")
                self.notifier.setEnabled(False)
                self.on_proc_terminated.emit()
        except BlockingIOError:
            pass
        except OSError as e:
            print(f"Error: {e}")
            self.notifier.setEnabled(False)

    def __read_full_chunk(self):
        result = ""
        while True:
            try:
                chunk = os.read(self.master_fd, 4096).decode(errors="ignore")
                if not chunk:
                    break
                result += chunk
            except BlockingIOError:
                break
            except OSError:
                break
        return result
