from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHBoxLayout


class RuleViewerPage(QWidget):
    def __init__(self, rules: list[str], parent=None):
        super().__init__(parent)
        self.rules = rules
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("<h2>Сгенерированные правила AppArmor</h2>")
        layout.addWidget(title)

        self.rule_table = QTableWidget()
        self.rule_table.setColumnCount(2)
        self.rule_table.setHorizontalHeaderLabels(["Тип", "Правило"])
        layout.addWidget(self.rule_table)

        # Кнопка обновления списка (на случай пересчёта)
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_rules)
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)
        self.refresh_rules()

    def refresh_rules(self):
        self.rule_table.setRowCount(0)
        for rule in self.rules:
            rule_type = self.get_rule_type(rule)
            row_position = self.rule_table.rowCount()
            self.rule_table.insertRow(row_position)
            self.rule_table.setItem(row_position, 0, QTableWidgetItem(rule_type))
            self.rule_table.setItem(row_position, 1, QTableWidgetItem(rule))

    def set_rules(self, rules: list[str]):
        self.rules = rules
        self.refresh_rules()

    def get_rule_type(self, rule: str) -> str:
        if rule.startswith("capability"):
            return "capability"
        if rule.startswith("network"):
            return "network"
        if rule.startswith("unix"):
            return "unix"
        if rule.startswith("userns"):
            return "userns"
        if rule.startswith("io_uring"):
            return "io_uring"
        if rule.startswith("mqueue"):
            return "mqueue"
        if rule.startswith("mount"):
            return "mount"
        if rule.startswith("pivot_root"):
            return "pivot_root"
        if rule.startswith("signal"):
            return "signal"
        if rule.startswith("ptrace"):
            return "ptrace"
        if rule.startswith("dbus"):
            return "dbus"
        if rule.startswith("change_profile"):
            return "change_profile"
        return "file"


# Пример использования (если запускать отдельно):
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    sample_rules = [
        "/usr/bin/curl ix,",
        "capability net_bind_service,",
        "network inet stream,",
        "userns (create),"
    ]
    viewer = RuleViewerPage(sample_rules)
    viewer.show()
    sys.exit(app.exec())