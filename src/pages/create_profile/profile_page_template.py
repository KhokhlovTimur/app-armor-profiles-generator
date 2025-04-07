import re

from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QWheelEvent
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QTextEdit

from src.apparmor.apparmor_parser import validate_and_load_profile
from src.util.apparmor_util import extract_profile_name


class ProfilePageTemplate(QWidget):
    finished = pyqtSignal()

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

    def save_profile(self, profile_as_string: str = None):
        profile_data = self.template_edit.toPlainText()
        try_save = validate_and_load_profile(profile_data, extract_profile_name(profile_data))
        self._check_profile(try_save, profile_as_string)

    def _check_profile(self, command_res, profile_as_string=None, success_msg="Профиль успешно сохранен и загружен!"):
        self.error_message = None
        if command_res.returncode == 0:
            QMessageBox.information(self, "Success", success_msg)
            if profile_as_string is None:
                pass
            else:
                self.template_edit.setPlainText(profile_as_string)
        else:
            self.error_message = self.filter_stderr(
                command_res.stderr) if command_res.stderr else "Неизвестная ошибка при проверке профиля."
            QMessageBox.warning(self, "Ошибка", f"Ошибка в профиле:\n{self.error_message}")

    def filter_stderr(self, stderr: str) -> str:
        stderr = stderr.strip()
        stderr = re.sub(r'^\[sudo\] пароль для .*?:\s*', '', stderr)
        return stderr

    def update_line_numbers(self):
        self.line_number_area.updateArea()

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
