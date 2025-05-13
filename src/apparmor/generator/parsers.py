import re


class RuleParser:
    def match(self, line: str) -> bool:
        raise NotImplementedError

    def generate(self, line: str) -> str | None:
        raise NotImplementedError


class CapabilityParser(RuleParser):
    pattern = re.compile(r'operation="capable".*capname="([^"]+)"')

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        match = self.pattern.search(line)
        if match:
            cap = match.group(1)
            if cap:
                return f"capability {cap},"
        return None


class NetworkParser(RuleParser):
    pattern = re.compile(
        r'operation="network".*family="([^"]+)".*sock_type="([^"]+)"(?:.*net_local_addr="([^"]+)")?(?:.*net_foreign_addr="([^"]+)")?(?:.*net_local_port="([^"]+)")?(?:.*net_foreign_port="([^"]+)")?'
    )

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        match = self.pattern.search(line)
        if not match:
            return None

        fam, sock, local_addr, foreign_addr, local_port, foreign_port = match.groups()

        if not fam or not sock:
            return None

        rule = f"network {fam} {sock}"

        if local_addr:
            rule += f" local_addr={local_addr}"
        if foreign_addr:
            rule += f" remote_addr={foreign_addr}"
        if local_port:
            rule += f" local_port={local_port}"
        if foreign_port:
            rule += f" remote_port={foreign_port}"

        return rule + ","


class DbusParser(RuleParser):
    dbus_re = re.compile(r'operation="dbus[^\"]*"')
    bus_re = re.compile(r'bus="([^"]+)"')
    path_re = re.compile(r'path="([^"]+)"')
    iface_re = re.compile(r'interface="([^"]+)"')
    member_re = re.compile(r'member="([^"]+)"')

    def match(self, line):
        return self.dbus_re.search(line)

    def generate(self, line):
        if not self.dbus_re.search(line):
            return None
        bus = self.bus_re.search(line)
        path = self.path_re.search(line)
        iface = self.iface_re.search(line)
        member = self.member_re.search(line)
        send_type = "send" if 'mask="send"' in line else "receive"
        if bus and path and iface and member:
            return f'dbus ({send_type}) bus={bus.group(1)} path="{path.group(1)}" interface="{iface.group(1)}" member="{member.group(1)}",'
        return None


class ExecParser(RuleParser):
    pattern = re.compile(r'operation="exec".*name="([^"]+)"')

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        match = self.pattern.search(line)
        if match:
            path = match.group(1)
            if path:
                return (path, 'ix')
        return None


class MountParser(RuleParser):
    mount_re = re.compile(r'operation="mount"')
    flags_re = re.compile(r'flags="([^"]+)"')
    fstype_re = re.compile(r'fstype="([^"]+)"')
    srcname_re = re.compile(r'srcname="([^"]+)"')
    dstname_re = re.compile(r'name="([^"]+)"')

    def match(self, line: str) -> bool:
        return bool(self.mount_re.search(line))

    def generate(self, line: str) -> str | None:
        if not self.mount_re.search(line):
            return None

        flags_match = self.flags_re.search(line)
        fstype_match = self.fstype_re.search(line)
        src_match = self.srcname_re.search(line)
        dst_match = self.dstname_re.search(line)

        options_part = ""
        fstype_part = ""
        src_part = ""
        dst_part = ""

        if flags_match:
            raw_flags = flags_match.group(1)
            flags = [f.strip() for f in raw_flags.split(",") if f.strip()]
            if len(flags) > 1:
                options_part = f"options=({','.join(flags)})"
            elif flags:
                options_part = f"options={flags[0]}"

        if fstype_match:
            fstype_part = f"fstype={fstype_match.group(1)}"

        if src_match:
            src_part = src_match.group(1)

        if dst_match:
            dst_part = f"-> {dst_match.group(1)}"

        parts = ["mount"]
        if options_part:
            parts.append(options_part)
        if fstype_part:
            parts.append(fstype_part)
        if src_part and dst_part:
            parts.append(src_part)
        if dst_part:
            parts.append(dst_part)

        return " ".join(parts)


class NetworkParser(RuleParser):
    pattern = re.compile(
        r'operation="([^"]+)"\s+.*class="net"[^"]*family="([^"]+)"(?:[^"]*sock_type="([^"]+)")?.*protocol=([0-9]+)'
    )

    allowed_permissions = {
        "create", "accept", "bind", "connect", "listen",
        "read", "write", "send", "receive", "shutdown"
    }

    protocol_map = {
        "6": "tcp",
        "17": "udp",
        "1": "icmp",
        "58": "icmpv6",
        "132": "sctp",
    }

    def match(self, line: str) -> bool:
        return bool(self.pattern.search(line))

    def generate(self, line: str) -> str | None:
        match = self.pattern.search(line)
        if not match:
            return None

        operation, family, sock_type, proto = match.groups()

        parts = ["network"]

        if operation in self.allowed_permissions:
            parts.append(f"({operation})")

        if family:
            parts.append(family)

        if sock_type:
            parts.append(sock_type)

        proto_name = self.protocol_map.get(proto)
        if proto_name:
            parts.append(proto_name)

        return " ".join(parts) + ","



class PivotRootParser(RuleParser):
    pattern = re.compile(r'operation="pivot_root".*name="([^"]+)"')

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        match = self.pattern.search(line)
        if match:
            src = match.group(1)
            if src:
                return f"pivot_root {src},"
        return None


class PtraceParser(RuleParser):
    pattern = re.compile(r'operation="ptrace".*peer="([^"]+)"')

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        match = self.pattern.search(line)
        if match:
            peer = match.group(1)
            if peer:
                return f"ptrace (trace) peer={peer},"
        return None


class SignalParser(RuleParser):
    pattern = re.compile(r'operation="signal".*peer="([^"]+)"')

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        match = self.pattern.search(line)
        if match:
            peer = match.group(1)
            if peer:
                return f"signal (send) peer={peer},"
        return None


class UserNsParser(RuleParser):
    pattern = re.compile(r'operation="userns_create"')

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        return "userns (create),"


class UnixRule(RuleParser):
    pattern = re.compile(r'operation="network".*family="unix".*sock_type="([^"]+)"')

    def match(self, line):
        return self.pattern.search(line)

    def generate(self, line):
        match = self.pattern.search(line)
        if match:
            sock = match.group(1)
            if sock:
                return f"unix (connect) type={sock},"
        return None
