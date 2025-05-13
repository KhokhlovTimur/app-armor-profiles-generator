from PyQt5.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QTextEdit
)

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage


class AdvancedRulesPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Custom rules")

        layout = QVBoxLayout()

        label = QLabel("Добавьте свои правила или измените настройки вручную:")
        layout.addWidget(label)

        input_layout = QHBoxLayout()
        self.rule_input_line_edit = QLineEdit()
        self.rule_input_line_edit.setPlaceholderText("Введите правило, например: /usr/bin/foo rix,")
        self.add_rule_button = QPushButton("Добавить")
        input_layout.addWidget(self.rule_input_line_edit)
        input_layout.addWidget(self.add_rule_button)
        layout.addLayout(input_layout)

        self.custom_rules_text_edit = QTextEdit()
        self.custom_rules_text_edit.setPlaceholderText("Дополнительные директивы AppArmor...")
        layout.addWidget(self.custom_rules_text_edit)

        self.setLayout(layout)

        self.add_rule_button.clicked.connect(self.add_custom_rule)

    def add_custom_rule(self):
        rule = self.rule_input_line_edit.text().strip() + ","
        if rule:
            current_text = self.custom_rules_text_edit.toPlainText().strip()
            updated = f"{current_text}\n{rule}" if current_text else rule
            self.custom_rules_text_edit.setPlainText(updated)
            self.rule_input_line_edit.clear()

    def get_profile_fragment(self) -> str:
        rules = self.custom_rules_text_edit.toPlainText().strip()
        if rules:
            return "\n".join(f"  {line}" for line in rules.splitlines())
        return ""