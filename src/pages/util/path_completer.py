import os

from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtWidgets import QCompleter


class ExecutablePathCompleter(QCompleter):
    def __init__(self, parent=None, only_binaries=True):
        super().__init__([], parent)
        self.only_binaries = only_binaries
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchContains)
        self.model = QStringListModel()
        self.setModel(self.model)

    def update_model(self, text):
        suggestions = []

        if os.path.isabs(text):
            dir_path = os.path.dirname(text) or "/"
            partial = os.path.basename(text)

            if os.path.isdir(dir_path):
                for entry in os.listdir(dir_path):
                    full = os.path.join(dir_path, entry)
                    if entry.lower().startswith(partial.lower()):
                        if self._match_filter(full):
                            suggestions.append(full)
        else:
            for directory in os.environ.get("PATH", "").split(":"):
                if not os.path.isdir(directory):
                    continue
                for entry in os.listdir(directory):
                    full = os.path.join(directory, entry)
                    if text.lower() in entry.lower():
                        if self._match_filter(full):
                            suggestions.append(full)

        self.model.setStringList(sorted(suggestions))

    def _match_filter(self, path):
        if self.only_binaries:
            return os.path.isfile(path) and os.access(path, os.X_OK)
        else:
            return os.path.isdir(path) or (os.path.isfile(path) and os.access(path, os.X_OK))