import re
from urllib.request import DataHandler

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox, QHBoxLayout, \
    QSplitter, QTextEdit
from PyQt5.QtGui import QFont, QPainter, QColor, QWheelEvent
from PyQt5.QtCore import Qt, QPoint

from src.app_armor.apparmor_parser import validate_and_load_profile
from src.pages.page_holder import PagesHolder


class ProfilePageTemplate(QWidget):
    def __init__(self):
        super().__init__()

    def select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setNameFilter("Все файлы (*.*)")
        file_dialog.setViewMode(QFileDialog.List)

        if file_dialog.exec_():
            self.file_path = file_dialog.selectedFiles()[0]
            print(f"Выбран путь и файл: {self.file_path}")
            return file_dialog.selectedFiles()[0]

        return None

    def increase_font_size(self):
        current_font = self.template_edit.font()
        current_font.setPointSize(current_font.pointSize() + 2)
        self.template_edit.setFont(current_font)

        self.line_number_area.setFont(current_font)
        self.line_number_area.update()

    def decrease_font_size(self):
        current_font = self.template_edit.font()
        current_font.setPointSize(current_font.pointSize() - 2)
        self.template_edit.setFont(current_font)

        self.line_number_area.setFont(current_font)
        self.line_number_area.update()

    def save_profile(self):
        profile_data = self.template_edit.toPlainText()
        try_save = validate_and_load_profile(profile_data, _extract_profile_name(profile_data))
        self._check_profile(try_save)

    def _check_profile(self, command_res):
        self.error_message = None
        if command_res.returncode == 0:
            QMessageBox.information(self, "Успех", f"Профиль успешно сохранен и загружен!")
            self.template_edit.setPlainText(self.get_default_template())
        else:
            self.error_message = self.filter_stderr(command_res.stderr) if command_res.stderr else "Неизвестная ошибка при проверке профиля."
            QMessageBox.warning(self, "Ошибка", f"Ошибка в профиле:\n{self.error_message}")

    def start_create_profile(self):
        # self.select_file()
        pass

    def filter_stderr(self, stderr: str) -> str:
        stderr = stderr.strip()
        stderr = re.sub(r'^\[sudo\] пароль для .*?:\s*', '', stderr)
        return stderr

    def update_line_numbers(self):
        self.line_number_area.updateArea()

    def import_profile(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setNameFilter("Все файлы (*)")
        file_dialog.setViewMode(QFileDialog.List)

        if file_dialog.exec_():
            self.file_path = file_dialog.selectedFiles()[0]
            print(f"Выбран путь и файл: {self.file_path}")
            if self.file_path:
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        self.template_edit.setPlainText(content)
                except Exception as e:
                    print(f"Ошибка при чтении файла: {e}")

        return None

def _extract_profile_name(profile_str: str) -> str | None:
    match = re.search(r'^\s*profile\s+([^\s]+)', profile_str, re.MULTILINE)
    if match:
        return match.group(1)
    return None


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFont(QFont("Courier", 10))
        self.setStyleSheet("background: lightgray;")
        self.setFixedWidth(40)

        self.editor.verticalScrollBar().valueChanged.connect(self.updateArea)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(0, 0, 0))

        block = self.editor.document().firstBlock()
        block_number = 1

        block_top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()

        scroll_top = self.editor.verticalScrollBar().value()
        scroll_bottom = scroll_top + self.editor.viewport().height()

        while block.isValid():
            block_height = self.editor.blockBoundingRect(block).height()
            block_bottom = block_top + block_height

            if block_top + block_height >= scroll_top and block_top <= scroll_bottom:
                painter.drawText(QPoint(int(self.width() - 30), int(block_top + block_height / 2) + 15),
                                 str(block_number))

            block = block.next()
            block_top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            block_number += 1

    def updateArea(self):
        self.update()


class ZoomableTextEdit(QTextEdit):
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoomIn()
            else:
                self.zoomOut()
        else:
            super().wheelEvent(event)
