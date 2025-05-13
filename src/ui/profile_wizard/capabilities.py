# capabilities_page.py
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QScrollArea, QWidget, QCheckBox
from PyQt5.QtCore import Qt

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage
from src.util.apparmor_rules_reader import get_existing_capabilities


class CapabilitiesPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Capabilities")
        self.capabilitiesCheckboxes = []

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите Capabilities:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        for cap in sorted(get_existing_capabilities()):
            cb = QCheckBox(cap)
            self.capabilitiesCheckboxes.append(cb)
            inner_layout.addWidget(cb)

        scroll.setWidget(inner)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def get_profile_fragment(self) -> str:
        selected = [cb.text() for cb in self.capabilitiesCheckboxes if cb.isChecked()]
        if selected:
            return "\n  # Capabilities\n" + "\n".join(f"  capability {cap}," for cap in selected) + "\n"
        return ""
