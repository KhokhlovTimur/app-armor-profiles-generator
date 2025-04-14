from typing import List, Tuple

from jinja2 import Environment, FileSystemLoader

from src.util.file_util import join_project_root

env = Environment(loader=FileSystemLoader(join_project_root("resources", "templates")))


class AppArmorProfile:
    def __init__(
            self,
            name: str = "",
            path: str = None,
            flags: str = "complain",
            includes=None,
            tunables=None,
            deny_rules: List[str] = None,
            disabled: bool = None,
            mode: str = "disabled",
            rules: List[Tuple[str, str]] = None,
            template_name: str = "new_profile_template.j2",
            full_code: str = None,
            all_rules: List[str] = None
    ):
        if includes is None:
            includes = ['abstractions/base']
        self.name = name
        self.path = path
        self.flags = flags
        self.includes = includes or []
        self.tunables = tunables or []
        self.all_rules = all_rules or []
        self.deny_rules = deny_rules or []
        self.rules = rules or []
        self.template = env.get_template(template_name)
        self.full_code = full_code
        self.disabled = disabled
        self.mode = mode

    def render(self) -> str:
        if self.full_code is not None:
            return self.full_code

        return self.template.render({
            "name": self.name,
            "app_path": self.path,
            "flags": self.flags,
            "includes": self.includes,
            "tunables": self.tunables,
            "deny_rules": self.deny_rules,
            "all_rules": self.all_rules,
            "rules": self.rules
        })

# def parse_profile_text(profile_text: str) -> AppArmorProfile:
#     header_match = re.search(r"profile\s+(\S+)\s+(\S+)\s+flags=\(([^)]+)\)", profile_text)
#     if not header_match:
#         raise ValueError("Не удалось найти заголовок профиля")
#
#     name, path, flags = header_match.groups()
#
#     includes = re.findall(r'^\s*include\s+<(.+?)>', profile_text, re.MULTILINE)
#
#     deny_rules = re.findall(r'^\s*deny\s+(.+?),', profile_text, re.MULTILINE)
#
#     rules = []
#     for match in re.finditer(r'^\s*(/[^ \n]+)\s+([rwxiklmacd]+),', profile_text, re.MULTILINE):
#         rules.append((match.group(1), match.group(2)))
#
#     return AppArmorProfile(
#         name=name,
#         path=path,
#         flags=flags,
#         includes=includes,
#         deny_rules=deny_rules,
#         rules=rules
#     )
