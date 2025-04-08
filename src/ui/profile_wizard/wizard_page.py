# base_wizard_page.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWizardPage

class AppArmorWizardPage(QWizardPage):
    show_profile_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page_id = ""

    def _on_show_profile_clicked(self):
        self.show_profile_clicked.emit()

    def set_page_id(self, page_id):
        self.page_id = page_id

    def get_profile_fragment(self) -> str:
        return ""