from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QDialog, QProgressBar, QLabel, QVBoxLayout

from src.apparmor.apparmor_manager import get_logs_not_empty, read_apparmor_profile_by_name
from src.apparmor.generator.generate_process_builder import analyze_profile_logs
from src.util.apparmor_util import extract_profile_path
from src.util.file_util import get_profile_created_or_modified_date


class LogLoaderThread(QThread):
    logs_loaded = pyqtSignal(list)

    def __init__(self, profile_name, parent=None, profile_path=None, is_from_script=None):
        super().__init__(parent)
        self.profile_name = profile_name
        self.profile_path = profile_path
        self.is_from_script = is_from_script

    def run(self):
        profile_text = read_apparmor_profile_by_name(self.profile_name)
        profile_path = extract_profile_path(profile_text)
        logs = []
        if self.is_from_script:
            self.run_from_script()
        else:
            logs = get_logs_not_empty(self.profile_name, profile_path, None)

        self.logs_loaded.emit(logs)

    def run_from_script(self):
        analyze_profile_logs(self.profile_name, get_profile_created_or_modified_date(self.profile_name))

class LogSearchDialog(QDialog):
    def __init__(self, profile_name, profile_path, on_logs_found, parent=None, is_from_script=None):
        super().__init__(parent)
        self.setWindowTitle("Поиск логов")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.layout = QVBoxLayout()
        self.label = QLabel("Поиск логов, подождите...")
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress)
        self.setLayout(self.layout)

        self.thread = LogLoaderThread(profile_name=profile_name, profile_path=profile_path, is_from_script=is_from_script)
        self.thread.finished.connect(self._on_logs_ready)
        self.on_logs_found = on_logs_found
        self.thread.start()

    def _on_logs_ready(self, logs=None):
        self.on_logs_found(logs)
        self.accept()