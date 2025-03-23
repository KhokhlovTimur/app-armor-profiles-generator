from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit, QPushButton, QHBoxLayout, QSplitter, QWidget

from src.pages.profile_page_template import ProfilePageTemplate, LineNumberArea, ZoomableTextEdit
from src.util.file_util import load_stylesheet


class AddProfilePage(ProfilePageTemplate):
    profile_template_path = "../../resources/profile_template.txt"
    __profile_styles = "add_profile_page.qss"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Profile")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        self.template_edit = QPlainTextEdit()
        self.template_edit.setObjectName("edit_text_area")
        load_stylesheet(self.__profile_styles, self.template_edit)
        self.template_edit.setPlainText(self.get_default_template())
        self.template_edit.setPlaceholderText("Enter or edit template...")

        self.line_number_area = LineNumberArea(self.template_edit)

        splitter.addWidget(self.line_number_area)
        splitter.addWidget(self.template_edit)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, stretch=1)

        self.buttons_layout = QHBoxLayout()
        self._add_buttons()
        self.buttons_container: QWidget = QWidget()
        self.buttons_container.setLayout(self.buttons_layout)

        load_stylesheet("buttons.qss", self.buttons_container)

        layout.addStretch()
        layout.addWidget(self.buttons_container)

        self.setLayout(layout)

        self.template_edit.textChanged.connect(self.update_line_numbers)

    def select_file(self):
        path = super().select_file()
        if path is not None:
            base = self.get_default_template()
            new = base.replace("${profile_name}", self.file_path.split('/')[-1]).replace("${profile_path}",
                                                                                 self.file_path)
            self.template_edit.setPlainText(new)

    def get_default_template(self):
        return ''.join(open(AddProfilePage.profile_template_path).readlines())

    def _add_buttons(self):
        self.increase_font_button = QPushButton("Increase font size", self)
        self.increase_font_button.clicked.connect(self.increase_font_size)
        self.buttons_layout.addWidget(self.increase_font_button)

        self.decrease_font_button = QPushButton("Decrease font size", self)
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        self.buttons_layout.addWidget(self.decrease_font_button)

        self.select_file_button = QPushButton("Choose file for profile", self)
        self.select_file_button.clicked.connect(self.select_file)
        self.buttons_layout.addWidget(self.select_file_button)

        self.import_file_button = QPushButton("Import", self)
        self.import_file_button.clicked.connect(self.import_profile)
        self.buttons_layout.addWidget(self.import_file_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_profile)
        self.buttons_layout.addWidget(self.save_button)
