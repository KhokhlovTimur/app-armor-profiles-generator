from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QSplitter
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtCore import Qt, QPoint

from src.app_armor.app_armor_parser import check_profile_correctness

profile_template_path = "../../resources/profile_template.txt"


class AddProfilePage(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Добавление нового профиля")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        self.template_edit = QPlainTextEdit(self)
        self.template_edit.setPlainText(self.get_default_template())
        self.template_edit.setPlaceholderText("Введите или отредактируйте шаблон...")

        self.line_number_area = LineNumberArea(self.template_edit)

        splitter.addWidget(self.line_number_area)
        splitter.addWidget(self.template_edit)

        layout.addWidget(splitter)

        font_layout = QHBoxLayout()

        self.increase_font_button = QPushButton("Увеличить шрифт", self)
        self.increase_font_button.clicked.connect(self.increase_font_size)
        font_layout.addWidget(self.increase_font_button)

        self.decrease_font_button = QPushButton("Уменьшить шрифт", self)
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        font_layout.addWidget(self.decrease_font_button)

        layout.addLayout(font_layout)

        self.select_file_button = QPushButton("Выбрать файл", self)
        self.select_file_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_file_button)

        self.save_button = QPushButton("Сохранить профиль", self)
        self.save_button.clicked.connect(self.save_profile)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        # Подключаем сигнал для обновления номеров строк при изменении текста
        self.template_edit.textChanged.connect(self.update_line_numbers)

    def get_default_template(self):
        return ''.join(open(profile_template_path).readlines())

    def select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setNameFilter("Все файлы (*.*)")
        file_dialog.setViewMode(QFileDialog.List)

        if file_dialog.exec_():
            self.file_path = file_dialog.selectedFiles()[0]
            base = self.get_default_template()
            new = base.replace("${profile_name}", self.file_path.split('/')[-1]).replace("${profile_path}",
                                                                                         self.file_path)
            self.template_edit.setPlainText(new)
            print(f"Выбран путь и файл: {self.file_path}")

    def increase_font_size(self):
        current_font = self.template_edit.font()
        current_font.setPointSize(current_font.pointSize() + 2)
        self.template_edit.setFont(current_font)

        # Увеличиваем размер шрифта для номеров строк
        self.line_number_area.setFont(current_font)
        self.line_number_area.update()

    def decrease_font_size(self):
        current_font = self.template_edit.font()
        current_font.setPointSize(current_font.pointSize() - 2)
        self.template_edit.setFont(current_font)

        # Уменьшаем размер шрифта для номеров строк
        self.line_number_area.setFont(current_font)
        self.line_number_area.update()

    def save_profile(self):
        profile_data = self.template_edit.toPlainText()
        try_save = check_profile_correctness(profile_data)
        if try_save.returncode == 0:
            QMessageBox.information(self, "Успех", f"Профиль успешно сохранен и загружен!")
            self.template_edit.setPlainText(self.get_default_template())
        else:
            error_message = try_save.stderr if try_save.stderr else "Неизвестная ошибка при проверке профиля."
            QMessageBox.warning(self, "Ошибка", f"Ошибка в профиле:\n{error_message}")

    def start_create_profile(self):
        # self.select_file()
        pass

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
                painter.drawText(QPoint(int(self.width() - 30), int(block_top + block_height / 2) + 4), str(block_number))

            block = block.next()
            block_top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            block_number += 1

    def updateArea(self):
        self.update()
