
import os
import re
import subprocess
from collections import defaultdict

from PyQt5.QtCore import Qt, pyqtSignal, QProcess, QStringListModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTreeWidget,
                             QTreeWidgetItem, QComboBox, QTextEdit, QFileDialog, QProgressBar, QDialog, QCompleter,
                             QMessageBox)

from src.pages.page_holder import PagesHolder
from src.pages.profile_generator import GeneratorPage
from src.util.command_executor_util import run_command
from src.util.file_util import load_stylesheet, load_stylesheet_buttons


class ProfileManager:
    tmp_profile_name = "tmp_profile"
    def __init__(self):
        self.profile_name = None
        self.profile_file = None

    def create_template_profile(self, bin_path):
        self.profile_name = self.tmp_profile_name
        return self.profile_name, self.profile_file

    def load_profile_complain(self):
        if self.profile_file:
            run_command(["sudo", "-S", "apparmor_parser", "-r", "-W", self.profile_file])
            run_command(["sudo", "-S", "aa-complain", self.profile_name])

    def load_profile_enforce(self):
        if self.profile_name:
            run_command(["sudo", "-S", "aa-enforce", self.profile_name])

    def update_profile(self, allow_rules, deny_rules):
        if not self.profile_file:
            return
        with open(self.profile_file, "r") as f:
            lines = f.readlines()
        insert_index = len(lines)
        for i, line in enumerate(lines):
            if line.strip() == "}":
                insert_index = i
                break

        new_rules_text = ""
        for rule in allow_rules:
            new_rules_text += rule + "\n"
        for rule in deny_rules:
            new_rules_text += "deny " + rule + "\n"
        lines.insert(insert_index, new_rules_text)
        with open(self.profile_file, "w") as f:
            f.writelines(lines)
        subprocess.run(["sudo", "apparmor_parser", "-r", "-W", self.profile_file])
        return "".join(lines)


class SelectGenerateProfilePage(QWidget):
    started = pyqtSignal(str, str, str)

    def __init__(self, stack, profile_mgr: ProfileManager, bin_path=None):
        super().__init__()
        self.mgr = profile_mgr
        self.bin_path = bin_path
        self.stack = stack

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        instr = QLabel("Укажите путь к программе для профилирования:")
        self.path_edit = QLineEdit()
        self.completer = ExecutablePathCompleter(self.path_edit)
        self.path_edit.setCompleter(self.completer)
        self.path_edit.textEdited.connect(self.completer.update_model)
        if bin_path is not None:
            self.path_edit.setText(bin_path)

        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_file)

        start_btn = QPushButton("Создать профиль и запустить")
        load_stylesheet_buttons(start_btn)
        start_btn.clicked.connect(self.on_start)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)

        layout.addWidget(instr)
        layout.addLayout(path_layout)
        # layout.addWidget(QLabel("Режим запуска приложения:"))
        layout.addWidget(start_btn)

        layout.addStretch()
        self.setLayout(layout)

    def setup_executable_path_completer(self, line_edit: QLineEdit):
        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)

        model = QStandardItemModel()

        paths = os.environ.get("PATH", "").split(":")
        seen = set()

        for directory in paths:
            if not os.path.isdir(directory):
                continue
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if full_path in seen:
                    continue
                if os.access(full_path, os.X_OK) and os.path.isfile(full_path):
                    seen.add(full_path)
                    item = QStandardItem(full_path)
                    model.appendRow(item)

        completer.setModel(model)
        line_edit.setCompleter(completer)

    def browse_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setNameFilter("Все файлы (*.*)")
        file_dialog.setViewMode(QFileDialog.List)

        if file_dialog.exec_():
            self.file_path = file_dialog.selectedFiles()[0]
            print(f"Выбран путь и файл: {self.file_path}")
            selected_file = file_dialog.selectedFiles()[0]
            # if os.access(selected_file, os.X_OK):
            self.path_edit.setText(selected_file)
            # else:
            #     QMessageBox.warning(self, "Ошибка", "Выбранный файл не является исполняемым.")

    def on_start(self):
        if not self.path_edit.text().strip():
            QMessageBox.warning(self, "Ошибка ввода", "Пожалуйста, выберите приложение.")
            return

        self.generation_page = GeneratorPage(self.stack, self, self.path_edit.text())
        PagesHolder().get_content_area().addWidget(self.generation_page)
        PagesHolder().get_content_area().setCurrentWidget(self.generation_page)
        # profiling_start_time = datetime.now().isoformat(sep=' ', timespec='seconds')
        # bin_path = self.path_edit.text().strip()
        # if not bin_path:
        #     return
        # profile_name, profile_file = self.mgr.create_template_profile(bin_path)
        # self.mgr.load_profile_complain()
        # mode = self.mode_combo.currentIndex()
        # cmd = ["aa-exec", "-p", profile_name, "--", bin_path]
        # if mode == 0:
        #     self.show_interactive_dialog(bin_path, profile_name, cmd)
        # else:
        #     run_command(["sudo", "-S", cmd])
        # print("emit")
        # self.started.emit(bin_path, profile_name, profiling_start_time)

    def show_interactive_dialog(self, bin_path, profile_name, cmd):
        self.process = QProcess(self)

        dialog = QDialog(self)
        dialog.setWindowTitle("Интерактивный запуск")
        dialog.setModal(True)
        dialog.setFixedSize(360, 140)

        layout = QVBoxLayout(dialog)
        label = QLabel("‍💻 Работайте с приложением.\nНажмите 'Завершить', когда закончите.")
        label.setAlignment(Qt.AlignCenter)

        progress = QProgressBar()
        progress.setRange(0, 0)  # бесконечная анимация

        done_button = QPushButton("✅ Завершить")
        done_button.clicked.connect(dialog.accept)

        layout.addWidget(label)
        layout.addWidget(progress)
        layout.addWidget(done_button)

        self.process.finished.connect(lambda: done_button.click())
        self.process.start("aa-exec", ["-p", profile_name, bin_path])

        dialog.exec_()

class ExecutablePathCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__([], parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchContains)
        self.model = QStringListModel()
        self.setModel(self.model)

    def update_model(self, text):
        suggestions = []

        if os.path.isabs(text):
            dir_path = os.path.dirname(text) or "/"
            if os.path.isdir(dir_path):
                for entry in os.listdir(dir_path):
                    full = os.path.join(dir_path, entry)
                    if os.path.isfile(full) and os.access(full, os.X_OK):
                        suggestions.append(full)
        else:
            for directory in os.environ.get("PATH", "").split(":"):
                if not os.path.isdir(directory):
                    continue
                for entry in os.listdir(directory):
                    full = os.path.join(directory, entry)
                    if os.path.isfile(full) and os.access(full, os.X_OK):
                        if text.lower() in entry.lower():
                            suggestions.append(full)

        self.model.setStringList(suggestions)

class LogMonitorPage(QWidget):
    profileReady = pyqtSignal(list, list)
    back_pressed = pyqtSignal()

    def __init__(self, profile_mgr: ProfileManager):
        super().__init__()
        self.mgr = profile_mgr
        layout = QVBoxLayout()
        title = QLabel("Обнаруженные события безопасности:")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Событие", "Действие"])
        categories = ["Файлы", "Сеть", "Capabilities", "Другие"]
        self.cat_items = {}
        for cat in categories:
            item = QTreeWidgetItem([cat])
            self.tree.addTopLevelItem(item)
            self.cat_items[cat] = item
        generate_btn = QPushButton("Сгенерировать профиль")
        back_btn = QPushButton("Back")
        generate_btn.clicked.connect(self.on_generate)
        back_btn.clicked.connect(lambda: self.back_pressed.emit())
        layout.addWidget(title)
        layout.addWidget(self.tree)
        layout.addWidget(generate_btn)
        layout.addWidget(back_btn)
        self.setLayout(layout)

    def add_event(self, category, description):
        if category not in self.cat_items:
            category = "Другие"
        parent = self.cat_items[category]
        item = QTreeWidgetItem(parent, [description])
        combo = QComboBox()
        combo.addItems(["Разрешить", "Запретить", "Игнорировать"])
        self.tree.setItemWidget(item, 1, combo)
        parent.addChild(item)

    def on_generate(self):
        allow_rules = []
        deny_rules = []
        for cat, parent in self.cat_items.items():
            for i in range(parent.childCount()):
                child = parent.child(i)
                action_widget = self.tree.itemWidget(child, 1)
                if action_widget:
                    action = action_widget.currentText()
                else:
                    action = "Игнорировать"
                event_text = child.text(0)
                if action == "Разрешить":
                    rule = event_text + ","
                    allow_rules.append(rule)
                elif action == "Запретить":
                    rule = event_text + ","
                    deny_rules.append(rule)
        self.profileReady.emit(allow_rules, deny_rules)

    def load_events_from_log(self, profile_name, start_time_iso="1 hour ago"):
        try:
            output = subprocess.check_output(
                ["journalctl", "-g", "apparmor", "--since", start_time_iso, "--no-pager"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8")
        except Exception as e:
            print("Ошибка чтения журнала:", e)
            return

        pattern = re.compile(
            r'apparmor="(DENIED|ALLOWED)".+?operation="(?P<op>[^"]+)"(?:.+?)?profile="(?P<profile>[^"]+)"(?:.+?)?name="(?P<name>[^"]+)"'
        )
        grouped = defaultdict(list)
        seen_entries = set()

        for line in output.splitlines():
            match = pattern.search(line)
            if not match:
                continue

            op = match.group("op")
            name = match.group("name")
            profile = match.group("profile")
            if not profile.endswith(profile_name):
                continue

            key = (op, name)
            if key in seen_entries:
                continue
            seen_entries.add(key)

            grouped[op].append({"operation": op, "path": name, "raw": line})

        self.tree.clear()
        self.cat_items.clear()

        for op_type, entries in grouped.items():
            parent = QTreeWidgetItem([f"{op_type} ({len(entries)})"])
            self.tree.addTopLevelItem(parent)
            self.cat_items[op_type] = parent
            for entry in entries:
                self.add_event(op_type, entry)

        self.tree.expandAll()

    def add_event(self, category, entry):
        if category not in self.cat_items:
            parent = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(parent)
            self.cat_items[category] = parent
        else:
            parent = self.cat_items[category]

        rule_text = self.generate_rule(entry)

        # Разделим путь и тип доступа
        if " " in rule_text:
            path, access = rule_text.rsplit(" ", 1)
        else:
            path, access = rule_text, ""

        # Оформим доступ жирным и цветным
        html = f"{path} <b><span style='color:#006400'>{access}</span></b>"

        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.DisplayRole, "")
        item.setData(0, Qt.UserRole, rule_text)  # сохраним оригинал

        # Используем QLabel с HTML
        label = QLabel()
        label.setTextFormat(Qt.RichText)
        label.setText(html)
        self.tree.setItemWidget(item, 0, label)

        combo = QComboBox()
        combo.addItems(["Разрешить", "Запретить", "Игнорировать"])
        self.tree.setItemWidget(item, 1, combo)

        parent.addChild(item)

    def generate_rule(self, entry):
        path = entry.get("path", "")
        op = entry.get("operation", "")

        if not path:
            return f"# Неизвестный путь для операции {op}"

        if op in ("open", "read"):
            return f"{path} r,"
        elif op == "write":
            return f"{path} w,"
        elif op == "append":
            return f"{path} a,"
        elif op == "file_mmap":
            return f"{path} mr,"
        elif op == "unlink":
            return f"{path} d,"
        elif op == "create":
            return f"{path} w,"
        elif op == "truncate":
            return f"{path} w,"
        elif op == "rename":
            return f"{path} w,"
        elif op == "chmod":
            return f"{path} w,"
        elif op == "chown":
            return f"{path} w,"
        elif op == "getattr":
            return f"{path} r,"

        elif op in ("exec", "execute"):
            return f"{path} ix,"  # может быть также Px, Cx, ux в зависимости от желания

        elif op in ("connect", "sendmsg", "recvmsg"):
            return f"network inet stream,"
        elif op in ("accept",):
            return f"network inet stream,"
        elif op == "bind":
            return f"network inet stream,"

        elif op == "capable":
            cap_match = re.search(r'capname="([^"]+)"', entry.get("raw", ""))
            capname = cap_match.group(1) if cap_match else "unknown"
            return f"capability {capname},"

        elif op == "signal":
            return f"signal {path},"

        elif op == "mount":
            return f"mount {path},"

        elif op == "ptrace":
            return f"ptrace {path},"

        elif op in ("shm_read", "shm_write", "ipc"):
            return f"{path} rw,"

        return f"# ❓ Неизвестная операция: {op} → {path}"


class ProfileDiffPage(QWidget):
    applyChanges = pyqtSignal()
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Предпросмотр нового профиля:"))
        self.diff_edit = QTextEdit()
        self.diff_edit.setReadOnly(True)
        layout.addWidget(self.diff_edit)
        apply_btn = QPushButton("Применить профиль")
        apply_btn.clicked.connect(lambda: self.applyChanges.emit())
        layout.addWidget(apply_btn)
        self.setLayout(layout)

    def show_diff(self, new_profile_text):
        """Отображаем текст нового профиля (или дифф)."""
        # В простейшем случае показываем весь текст профиля
        self.diff_edit.setText(new_profile_text)
        # (Можно реализовать дифф с прошлой версией и подсветкой)
