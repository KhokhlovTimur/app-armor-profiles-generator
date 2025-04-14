# import os
# import re
#
# from PyQt5.QtCore import pyqtSignal
# from PyQt5.QtWidgets import (
#     QWidget, QVBoxLayout, QPushButton,
#     QPlainTextEdit, QLineEdit, QLabel, QHBoxLayout, QTabWidget,
#     QDialog, QMessageBox
# )
#
# from src.apparmor.generator.profile_generator import ProfileFromLogsGenerator
# from src.util.file_util import load_stylesheet, load_stylesheet_buttons
#
#
# def parse_options_line(options_text):
#     segments = options_text.split("/")
#     results = []
#     for seg in segments:
#         seg = seg.strip(" []").strip()
#         match = re.search(r"\((\w)\)", seg)
#         if match:
#             letter = match.group(1)
#             option_label = seg
#             results.append((letter, option_label))
#     return results
#
# class GeneratorPage(QWidget):
#     update_signal = pyqtSignal()
#     finished = pyqtSignal()
#
#     def __init__(self, bin_path):
#         super().__init__()
#         self.is_reject_all = False
#         self.is_accept_all = False
#         # self.update_signal.connect(self.flush_output)
#         self.binary = bin_path
#         self.last_text_input = ""
#         self.setGeometry(200, 200, 900, 600)
#
#         main_layout = QVBoxLayout()
#         self.setLayout(main_layout)
#
#         self.output = QPlainTextEdit()
#         self.output.setReadOnly(True)
#         main_layout.addWidget(self.output)
#
#         input_layout = QHBoxLayout()
#         self.input_line = QLineEdit()
#         self.input_line.setPlaceholderText("Введите A / D / I / G / E / N / Т / R / F и нажмите Enter")
#         self.input_line.returnPressed.connect(self.send_input)
#         input_layout.addWidget(QLabel("Ввод:"))
#         input_layout.addWidget(self.input_line)
#         main_layout.addLayout(input_layout)
#
#         self.tab_widget = QTabWidget()
#         main_layout.addWidget(self.tab_widget)
#
#         self.terminate_button = QPushButton("Terminate")
#         self.accept_all_button = QPushButton("Accept All")
#         self.reject_all_button = QPushButton("Reject All")
#         load_stylesheet_buttons(self.terminate_button)
#         load_stylesheet_buttons(self.accept_all_button)
#         load_stylesheet_buttons(self.reject_all_button)
#
#         self.accept_all_button.pressed.connect(self.accept_all)
#         self.reject_all_button.pressed.connect(self.reject_all)
#         self.terminate_button.pressed.connect(self.terminate_proc)
#
#         button_layout = QHBoxLayout()
#         button_layout.addWidget(self.accept_all_button)
#         button_layout.addWidget(self.reject_all_button)
#         main_layout.addLayout(button_layout)
#
#         main_layout.addWidget(self.terminate_button)
#
#         self.process = None
#         self.master_fd = None
#         self.thread = None
#         self.output_buffer = ""
#         self.interactive_buffer = ""
#
#         self.processed_entries = set()
#         self.prcessed_paths = set()
#         self.rule_count = 1
#
#         self.run_generate()
#
#     def run_generate(self):
#         if self.process:
#             self.output.appendPlainText("Процесс уже запущен")
#             return
#
#         self.generator = ProfileFromLogsGenerator()
#         command_res = self.generator.start_generate(self.binary)
#
#         if command_res.returncode == 0:
#             pass
#         else:
#             self.error_message = self.filter_stderr(
#                 command_res.stderr) if command_res.stderr else "Неизвестная ошибка при проверке профиля."
#             QMessageBox.warning(self, "Error", f"\n{self.error_message}")
#             self.terminate_proc()
#             return
#
#         self.generator.exec_app(self)
#         self.process, self.master_fd = self.generator.run_generate()
#         self.generator.on_data_received.connect(lambda f: self.flush_output(f))
#         self.generator.on_proc_terminated.connect(self.terminate_proc)
#
#         self.output_buffer = ""
#         self.output.clear()
#         self.output.appendPlainText(f"Running for {self.binary}...\n")
#         self.first_text_received = False
#         self.exec_app_called = False
#         self.is_last_dialog = False
#
#     def filter_stderr(self, stderr: str) -> str:
#         stderr = stderr.strip()
#         stderr = re.sub(r'^\[sudo\] пароль для .*?:\s*', '', stderr)
#         return stderr
#
#     def terminate_proc(self):
#         if self.process and self.process.poll() is None:
#             self.process.terminate()
#             self.output.appendPlainText("")
#         else:
#             self.output.appendPlainText("")
#
#         self.finished.emit()
#         self.deleteLater()
#
#     def accept_all(self):
#         self.is_accept_all = True
#         self.send_input("A")
#
#     def reject_all(self):
#         self.is_reject_all = True
#         self.send_input("B")
#
#     def flush_output(self, output_buffer=None):
#         if not output_buffer:
#             return
#
#         if self.is_last_dialog:
#             self.output.appendPlainText(output_buffer)
#
#         self.curr_buffer = output_buffer
#         self.interactive_buffer += output_buffer
#         output_buffer= ""
#         self.is_last_dialog = False
#         executed = False
#         if self.is_last_dialog and self.binary in self.curr_buffer:
#             os.write(self.master_fd, b"\n")
#
#         new_rule_pattern = re.compile(
#             r"((?:\S+:\s*.*\n)+)"
#             r"(\(A\).*?(?:\n|$))",
#             re.DOTALL
#         )
#
#         for match in new_rule_pattern.finditer(self.curr_buffer):
#             executed = True
#             info_text = match.group(1).strip()
#             options_text = match.group(2).strip()
#             key = info_text + "||" + options_text
#             row1 = self.curr_buffer.strip().splitlines()[1]
#             if key not in self.processed_entries and row1 not in self.prcessed_paths:
#                 self.add_interactive_entry(info_text, options_text)
#                 self.processed_entries.add(key)
#                 self.prcessed_paths.add(row1)
#             elif row1 in self.prcessed_paths:
#                 self.update_interactive_entry(info_text, options_text)
#
#             self._check_flags()
#             curr_buffer = ""
#
#         dialog_pattern = re.compile(
#             r"(.*?\?)\s*\n*(?:\[.*?\]\s*\n*)*([\s\S]*[\(\[][\w\d]+[\)\]][^\n]*)",
#             re.DOTALL
#         )
#         match = re.search(dialog_pattern, self.curr_buffer)
#         if not executed and match:
#             executed = True
#             info_text = match.group(1).strip()
#             options_text = match.group(2).strip()
#             self.is_last_dialog = True
#             self.show_non_rule_dialog(info_text, options_text)
#             curr_buffer = ""
#
#         # if not executed and bool(re.search(r"[\[\(][A-Z0-9][\]\)]", self.curr_buffer)) and self.exec_app_called:
#         #     self.output.appendPlainText(self.curr_buffer)
#
#         # if not self.exec_app_called and self.first_text_received:
#         #     print(f'exec {self.binary}')
#         #
#         #     def delayed_exec():
#         #         self.exec_app()
#         #
#         #     QTimer.singleShot(2000, delayed_exec)
#         #     self.exec_app_called = True
#
#     def check_generated_logs(self):
#         self.send_input("S")
#
#     def _check_flags(self):
#         print("Check flags")
#         if self.is_accept_all:
#             self.send_input("A")
#         elif self.is_reject_all:
#             self.send_input("D")
#
#     def add_interactive_entry(self, info_text, options_text):
#         widget = InteractiveEntryWidget(info_text, options_text, self.send_command)
#         tab_name = f"{self.rule_count}"
#         self.rule_count += 1
#         index = self.tab_widget.addTab(widget, tab_name)
#         self.tab_widget.setCurrentIndex(index)
#
#     def update_interactive_entry(self, info_text, options_text):
#         widget = InteractiveEntryWidget(info_text, options_text, self.send_command)
#         tab_name = f"{self.rule_count - 1}"
#         if not self.tab_widget:
#             return
#         index = self.tab_widget.count() - 1
#         self.tab_widget.removeTab(index)
#         self.tab_widget.insertTab(index, widget, tab_name)
#         self.tab_widget.setCurrentIndex(index)
#
#     def show_non_rule_dialog(self, info_text, options_text):
#         dialog = NonRuleDialog(info_text, options_text, self)
#         if dialog.exec_() == QDialog.Accepted and dialog.selected_command:
#             self.send_command(dialog.selected_command, None)
#
#     def send_command(self, command, widget):
#         if not self.master_fd:
#             self.output.appendPlainText("Процесс не запущен")
#             return
#         try:
#             self.last_text_input = command
#             os.write(self.master_fd, (command).encode())
#             self.output.appendPlainText(f"Отправлена команда: {command}")
#         except Exception as e:
#             self.output.appendPlainText(f"Ошибка при отправке команды: {e}")
#
#     def send_input(self, text=None):
#         if not self.master_fd:
#             self.output.appendPlainText("Процесс не запущен")
#             return
#         if text is None:
#             text = self.input_line.text().strip()
#         if text:
#             self.last_text_input = text
#             os.write(self.master_fd, (text).encode())
#             self.output.appendPlainText(f"Ввод: {text}")
#             self.input_line.clear()
#
# class NonRuleDialog(QDialog):
#     def __init__(self, info_text, options_text, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Действия с профилем")
#         self.selected_command = None
#
#         layout = QVBoxLayout(self)
#
#         info_label = QLabel(info_text)
#         info_label.setWordWrap(True)
#         layout.addWidget(info_label)
#
#         buttons_layout = QHBoxLayout()
#         options = parse_options_line(options_text)
#         for letter, label in options:
#             btn = QPushButton(f"{label}")
#             btn.clicked.connect(lambda _, cmd=letter: self.on_button_clicked(cmd))
#             buttons_layout.addWidget(btn)
#         layout.addLayout(buttons_layout)
#
#     def on_button_clicked(self, command):
#         self.selected_command = command
#         self.accept()
#
# class InteractiveEntryWidget(QWidget):
#     def __init__(self, info_text, options_text, command_callback):
#         super().__init__()
#         self.command_callback = command_callback
#         self.selected_command = None
#
#         layout = QVBoxLayout()
#         self.setLayout(layout)
#
#         self.info_label = QLabel(info_text)
#         self.info_label.setWordWrap(True)
#         layout.addWidget(self.info_label)
#
#         self.choice_label = QLabel("-")
#         layout.addWidget(self.choice_label)
#
#         buttons_layout = QHBoxLayout()
#         options = parse_options_line(options_text)
#         self.buttons = []
#         for index, (letter, label) in enumerate(options):
#             btn = QPushButton(f"{label}")
#             load_stylesheet("buttons.qss", btn)
#             btn.clicked.connect(lambda _, cmd=letter, idx=index: self.on_button_clicked(cmd, idx))
#             self.buttons.append(btn)
#             buttons_layout.addWidget(btn)
#         layout.addLayout(buttons_layout)
#
#     def on_button_clicked(self, command, index):
#         self.selected_command = command
#         self.choice_label.setText(f"Selected: {command}")
#         self.command_callback(command, self)
