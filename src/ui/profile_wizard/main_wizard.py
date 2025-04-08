import sys
from typing import List

from PyQt5.QtWidgets import (
    QApplication, QWizard
)

from src.ui.profile_wizard.abstractions import AbstractionsPage
from src.ui.profile_wizard.capabilities import CapabilitiesPage
from src.ui.profile_wizard.custom_rules import AdvancedRulesPage
from src.ui.profile_wizard.execute_rules import ExecuteRulesPage
from src.ui.profile_wizard.last_options_page import LastOptionsPage
from src.ui.profile_wizard.mount import MountRulesPage
from src.ui.profile_wizard.network import NetworkRulesPage
from src.ui.profile_wizard.profile_info import ProfileInfoPage
from src.ui.profile_wizard.tunables import TunablesPage
from src.ui.profile_wizard.wizard_page import AppArmorWizardPage


class AppArmorWizard(QWizard):
    def __init__(self, parent=None):
        super(AppArmorWizard, self).__init__(parent)
        self.setWindowTitle("AppArmor Profile Wizard")
        self.resize(600, 500)
        self.app_path = ""
        self.flags = ""

        self.last_page = LastOptionsPage()
        self.pages: List[AppArmorWizardPage]  = [ProfileInfoPage(), TunablesPage(), CapabilitiesPage(), AbstractionsPage(), NetworkRulesPage(), ExecuteRulesPage(), MountRulesPage(), AdvancedRulesPage(), self.last_page]

        for page in self.pages:
            page_id = self.addPage(page)
            page.set_page_id(page_id)

        # self.currentIdChanged.connect(self.on_page_changed)

    def on_page_changed(self, page_id):
        if page_id == self.last_page.page_id:
            print("12")
            self.last_page.set_data(self.pages)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = AppArmorWizard()
    wizard.show()
    sys.exit(app.exec_())
