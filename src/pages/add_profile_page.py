from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QMessageBox, QHBoxLayout

from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class AddProfilePage(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Добавление нового профиля")
        self.setGeometry(200, 200, 400, 300)

        # Создаем вертикальный макет
        layout = QVBoxLayout()

        # Создаем текстовое поле для шаблона
        self.template_edit = QTextEdit(self)
        self.template_edit.setPlainText(self.get_default_template())  # Устанавливаем шаблон по умолчанию
        self.template_edit.setPlaceholderText("Введите или отредактируйте шаблон...")  # Подсказка для пользователя
        layout.addWidget(self.template_edit)

        # Создаем горизонтальный макет для кнопок
        font_layout = QHBoxLayout()

        # Кнопка для увеличения шрифта
        self.increase_font_button = QPushButton("Увеличить шрифт", self)
        self.increase_font_button.clicked.connect(self.increase_font_size)
        font_layout.addWidget(self.increase_font_button)

        # Кнопка для уменьшения шрифта
        self.decrease_font_button = QPushButton("Уменьшить шрифт", self)
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        font_layout.addWidget(self.decrease_font_button)

        # Добавляем горизонтальный макет с кнопками в основной вертикальный макет
        layout.addLayout(font_layout)

        self.select_file_button = QPushButton("Выбрать файл", self)
        self.select_file_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_file_button)

        # Кнопка для сохранения профиля
        self.save_button = QPushButton("Сохранить профиль", self)
        self.save_button.clicked.connect(self.save_profile)
        layout.addWidget(self.save_button)

        # Устанавливаем макет в окно
        self.setLayout(layout)

    def get_default_template(self):
        # Шаблон для текстового поля, как в вашем примере
        return '''abi <abi/4.0>,
    include <tunables/global>

    profile Discord /usr/share/discord/Discord flags=(unconfined) {
      userns,

      # Site-specific additions and overrides. See local/README for details.
      include if exists <local/Discord>
    }
    '''

    def select_file(self):
        pass
        # Открываем диалог для выбора пути и имени файла
        # file_dialog = QFileDialog(self)
        # file_dialog.setFileMode(QFileDialog.AnyFile)  # Открываем для выбора файла
        # file_dialog.setAcceptMode(QFileDialog.AnyFile)  # Режим для сохранения файла
        # file_dialog.setNameFilter("Все файлы (*.*)")  # Фильтр для всех файлов
        #
        # # Если пользователь выбрал файл
        # if file_dialog.exec_():
        #     self.file_path = file_dialog.selectedFiles()[0]  # Получаем путь к выбранному файлу
        #     print(f"Выбран путь и файл: {self.file_path}")


    def increase_font_size(self):
        # Получаем текущий шрифт и увеличиваем его размер
        current_font = self.template_edit.font()
        current_font.setPointSize(current_font.pointSize() + 2)  # Увеличиваем размер на 2
        self.template_edit.setFont(current_font)

    def decrease_font_size(self):
        # Получаем текущий шрифт и уменьшаем его размер
        current_font = self.template_edit.font()
        current_font.setPointSize(current_font.pointSize() - 2)  # Уменьшаем размер на 2
        self.template_edit.setFont(current_font)

    def save_profile(self):
        # Получаем текст из текстового поля
        profile_data = self.template_edit.toPlainText()

        # Здесь можно добавить логику для сохранения профиля
        if profile_data.strip():  # Проверяем, что текст не пустой
            # Пример сохранения в файл (можно адаптировать под вашу задачу)
            with open("new_profile.txt", "w") as f:
                f.write(profile_data)
            QMessageBox.information(self, "Успех", "Профиль успешно сохранен!")
        else:
            QMessageBox.warning(self, "Ошибка", "Шаблон не может быть пустым!")


def save_profile(self):
        # Получаем текст из текстового поля
        profile_data = self.template_edit.toPlainText()

        # Здесь можно добавить логику для сохранения профиля
        if profile_data.strip():  # Проверяем, что текст не пустой
            # Пример сохранения в файл (можно адаптировать под вашу задачу)
            with open("new_profile.txt", "w") as f:
                f.write(profile_data)
            QMessageBox.information(self, "Успех", "Профиль успешно сохранен!")
        else:
            QMessageBox.warning(self, "Ошибка", "Шаблон не может быть пустым!")
