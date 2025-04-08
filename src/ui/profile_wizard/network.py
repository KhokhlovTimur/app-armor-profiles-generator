from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QComboBox, QListWidget, QLabel, QVBoxLayout, QPushButton

from src.ui.profile_wizard.wizard_page import AppArmorWizardPage


class NetworkRulesPage(AppArmorWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Расширенные сетевые правила")

        self.layout = QVBoxLayout()
        self.entries = []

        self.layout.addWidget(QLabel("Добавьте сетевые правила (permissions, domain, type, protocol):"))
        self.entry_list = QListWidget()
        self.layout.addWidget(self.entry_list)

        form_layout = QHBoxLayout()

        self.perms_combo = QComboBox()
        self.perms_combo.setEditable(True)
        self.perms_combo.setInsertPolicy(QComboBox.NoInsert)
        self.perms_combo.addItems([
            "create", "accept", "bind", "connect", "listen", "read", "write",
            "send", "receive", "getsockname", "getpeername", "getsockopt",
            "setsockopt", "fcntl", "ioctl", "shutdown", "getpeersec"
        ])
        self.perms_input = QLineEdit()
        self.perms_input.setPlaceholderText("Выбранные пермишены, через запятую")

        # Domain
        self.domain_input = QComboBox()
        self.domain_input.setEditable(True)
        self.domain_input.addItems([
            "", "inet", "ax25", "ipx", "appletalk", "netrom", "bridge", "atmpvc",
            "x25", "inet6", "rose", "netbeui", "security", "key", "packet", "ash",
            "econet", "atmsvc", "sna", "irda", "pppox", "wanpipe", "bluetooth"
        ])

        # Type
        self.type_input = QComboBox()
        self.type_input.setEditable(True)
        self.type_input.addItems(["", "stream", "dgram", "seqpacket", "raw", "rdm", "packet", "dccp"])

        # Protocol
        self.protocol_input = QComboBox()
        self.protocol_input.setEditable(True)
        self.protocol_input.addItems([
            "", "tcp", "udp", "icmp", "icmpv6", "sctp", "dccp", "igmp",
            "esp", "ah", "gre", "ipip", "ospf", "pim", "vrrp", "udplite"
        ])

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_entry)

        remove_button = QPushButton("Удалить выбранное")
        remove_button.clicked.connect(self.remove_selected_entry)

        form_layout.addWidget(self.perms_input)
        form_layout.addWidget(self.domain_input)
        form_layout.addWidget(self.type_input)
        form_layout.addWidget(self.protocol_input)
        form_layout.addWidget(add_button)
        form_layout.addWidget(remove_button)

        self.layout.addWidget(QLabel("Permissions:"))
        self.layout.addWidget(self.perms_input)
        self.layout.addWidget(self.perms_combo)
        self.layout.addWidget(QLabel("Domain:"))
        self.layout.addWidget(self.domain_input)
        self.layout.addWidget(QLabel("Type:"))
        self.layout.addWidget(self.type_input)
        self.layout.addWidget(QLabel("Protocol:"))
        self.layout.addWidget(self.protocol_input)

        self.layout.addLayout(form_layout)
        self.perms_combo.activated.connect(self.append_permission)

        self.setLayout(self.layout)

    def remove_selected_entry(self):
        selected = self.entry_list.currentRow()
        if selected >= 0:
            self.entry_list.takeItem(selected)
            del self.entries[selected]

    def append_permission(self):
        perm = self.perms_combo.currentText()
        existing = self.perms_input.text().strip()
        perms = [p.strip() for p in existing.split(',') if p.strip()]
        if perm not in perms:
            perms.append(perm)
            self.perms_input.setText(", ".join(perms))

    def add_entry(self):
        perms = self.perms_input.text().strip()
        domain = self.domain_input.currentText().strip()
        net_type = self.type_input.currentText().strip()
        protocol = self.protocol_input.currentText().strip()

        parts = ["network"]
        if perms:
            parts.append(f"({perms})")
        if domain:
            parts.append(domain)
        if net_type:
            parts.append(net_type)
        if protocol:
            parts.append(protocol)

        rule = " ".join(parts) + ","
        self.entry_list.addItem(rule)
        self.entries.append(rule)

        self.perms_input.clear()
        self.domain_input.setCurrentIndex(0)
        self.type_input.setCurrentIndex(0)
        self.protocol_input.setCurrentIndex(0)

    def get_profile_fragment(self):
        if not self.entries:
            return ""
        return "\n" + "\n".join(f"  {line}" for line in self.entries)
