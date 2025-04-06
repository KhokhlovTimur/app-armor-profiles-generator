from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox, QComboBox
)
from PyQt5.QtCore import pyqtSignal

class ExclusionEditorWidget(QWidget):
    exclusions_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.setLayout(QVBoxLayout())

        self.exclusions = {
            "/home": {},
            "/root": {},
            "/tmp": {},
            "/mnt": {},
            "/etc/shadow": {},
        }

        self.checkboxes = {}
        self.single_active = False  # <-- флаг

        for path in self.exclusions:
            cb = QCheckBox(f"Запретить доступ к {path}")
            cb.stateChanged.connect(lambda state, p=path: self._on_toggle(p, state))
            self.layout().addWidget(cb)

            label = QLabel("  Разрешённые ресурсы:")
            label.setVisible(False)
            self.layout().addWidget(label)

            lw = QListWidget()
            lw.setVisible(False)
            self.layout().addWidget(lw)

            input_layout = QHBoxLayout()
            line = QLineEdit()
            add = QPushButton("+")
            line.setVisible(False)
            add.setVisible(False)
            add.clicked.connect(lambda _, p=path, l=line, w=lw: self._add_exception(p, l, w))
            input_layout.addWidget(line)
            input_layout.addWidget(add)
            self.layout().addLayout(input_layout)

            self.exclusions[path] = {
                "checkbox": cb,
                "label": label,
                "list": lw,
                "input": line,
                "button": add,
                "exceptions": []
            }

        apply_btn = QPushButton("Применить исключения")
        apply_btn.clicked.connect(self._emit_exclusions)
        self.layout().addWidget(apply_btn)

    def set_single_active_mode(self, enable: bool):
        self.single_active = enable

    def _on_toggle(self, path, state):
        data = self.exclusions[path]

        if self.single_active and state:
            # отключаем все остальные
            for other_path, other_data in self.exclusions.items():
                if other_path != path:
                    other_data["checkbox"].blockSignals(True)
                    other_data["checkbox"].setChecked(False)
                    other_data["checkbox"].blockSignals(False)
                    self._set_visible(other_path, False)

        self._set_visible(path, bool(state))

    def _set_visible(self, path, visible):
        data = self.exclusions[path]
        data["label"].setVisible(visible)
        data["list"].setVisible(visible)
        data["input"].setVisible(visible)
        data["button"].setVisible(visible)

    def _add_exception(self, path, line_edit, list_widget):
        text = line_edit.text().strip()
        if not text:
            return
        item = QListWidgetItem(text)
        list_widget.addItem(item)
        self.exclusions[path]["exceptions"].append(text)
        line_edit.clear()

    def _emit_exclusions(self):
        result = {}
        for path, data in self.exclusions.items():
            if data["checkbox"].isChecked():
                result[path] = {
                    "exceptions": data["exceptions"]
                }
        if not result:
            QMessageBox.information(self, "Пусто", "Вы не выбрали ни одного исключения.")
        else:
            self.exclusions_updated.emit(result)


from jinja2 import Environment, DictLoader
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QPlainTextEdit

class ProfileGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор профиля AppArmor")
        self.setMinimumSize(800, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.template_selector = QComboBox()
        self.template_selector.addItems(["server", "desktop", "network-app", "minimal"])
        self.layout.addWidget(self.template_selector)

        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(False)
        self.layout.addWidget(self.editor)

        self.exclude_editor = ExclusionEditorWidget()
        self.exclude_editor.set_single_active_mode(True)
        self.layout.addWidget(self.exclude_editor)

        self.generate_button = QPushButton("Сгенерировать профиль")
        self.generate_button.clicked.connect(self.generate_profile)
        self.layout.addWidget(self.generate_button)

        self.exclude_editor.exclusions_updated.connect(self.update_exclusions)

        self.exclusions = {}

        self.env = Environment(loader=DictLoader({"complex_profile.j2": self.template_text()}))
        self.template = self.env.get_template("complex_profile.j2")

    def update_exclusions(self, data):
        self.exclusions = data

    def generate_profile(self):
        deny_rules = {path: "rw" for path in self.exclusions.keys()}
        allow_exceptions = {p: e for p, e in self.exclusions.items() if e}

        profile_type = self.template_selector.currentText()

        profiles = {
            "server": {
                "includes": [
                    "abstractions/base",
                    "abstractions/nameservice",
                    "abstractions/ssl_certs",
                    "abstractions/user-tmp",
                    "abstractions/ssh"
                ],
                "capabilities": [
                    "net_bind_service", "chown", "setgid", "setuid"
                ],
                "network_access": True
            },
            "desktop": {
                "includes": [
                    "abstractions/base",
                    "abstractions/X",
                    "abstractions/audio",
                    "abstractions/dbus-session",
                    "abstractions/user-download",
                    "abstractions/user-documents",
                    "abstractions/ssh"
                ],
                "capabilities": [
                    "sys_admin", "chown", "sys_chroot"
                ],
                "network_access": False
            },
            "network-app": {
                "includes": [
                    "abstractions/base",
                    "abstractions/nameservice",
                    "abstractions/user-tmp",
                    "abstractions/openssl",
                    "abstractions/ssh"
                ],
                "capabilities": [
                    "net_bind_service", "setuid", "setgid"
                ],
                "network_access": True
            },
            "minimal": {
                "includes": ["abstractions/base"],
                "capabilities": [],
                "network_access": False
            }
        }

        selected = profiles.get(profile_type, profiles["minimal"])

        allow_paths_by_section = []
        for section, exceptions in allow_exceptions.items():
            if isinstance(exceptions, dict):
                for path in exceptions.get("exceptions", []):
                    full_path = section.rstrip("/") + "/" + path.lstrip("/")
                    allow_paths_by_section.append((full_path, "r"))

        context = {
            "app_path": "/usr/bin/my-secure-app",
            "flags": "complain",
            "includes": selected["includes"],
            "capabilities": selected["capabilities"],
            "allow_rules": [
                ("/etc/myapp/config.yml", "r"),
                ("/var/log/myapp.log", "w"),
                ("/usr/share/myapp/**", "r"),
                ("/tmp/myapp/**", "rw"),
            ] + allow_paths_by_section,
            "deny_rules": deny_rules,
            "allow_exceptions": {},
            "network_access": selected["network_access"]
        }

        profile = self.template.render(**context)
        self.editor.setPlainText(profile)

    def template_text(self):
        return """
#include <tunables/global>

profile {{ app_path }} flags=({{ flags }}) {

  # ========== Абстракции ==========
  {% for inc in includes %}
  include <{{ inc }}>
  {% endfor %}

  # ========== Возможности (capabilities) ==========
  {% for cap in capabilities %}
  capability {{ cap }},
  {% endfor %}

  # ========== Разрешённые доступы ==========
  {% for path, perms in allow_rules %}
  {{ path }} {{ perms }},
  {% endfor %}

  # ========== Явные исключения ==========
  {% for path, perms in deny_rules.items() %}
  deny {{ path }} {{ perms }},
  {% endfor %}

  # ========== Сеть ==========
  {% if network_access %}
  network inet stream,
  {% else %}
  deny network,
  {% endif %}
}
"""

import sys
from PyQt5.QtWidgets import QApplication
def main():
    app = QApplication(sys.argv)
    win = ProfileGeneratorWidget()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
