import copy
import re
from typing import List, Tuple

from jinja2 import Environment, FileSystemLoader

from src.apparmor.apparmor_manager import read_apparmor_profile_by_name
from src.constants import PROFILES_PATH
from src.util.file_util import join_project_root

env = Environment(loader=FileSystemLoader(join_project_root("resources", "templates")), trim_blocks=True,
    lstrip_blocks=True)

class AppArmorProfile:
    def __init__(
            self,
            name: str = "",
            path: str = None,
            flags: List[str] = None,
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
        self.includes = set(includes or ['abstractions/base'])
        self.tunables = set(tunables or [])
        self.all_rules = set(all_rules or [])
        self.deny_rules = set(deny_rules or [])
        self.rules = set(rules or [])
        self.template = env.get_template(template_name)
        self.full_code = full_code
        self.disabled = disabled
        self.mode = mode
        self.tunables.add('tunables/global')
        self.includes.add('abstractions/base')

    def render(self) -> str:
        if self.full_code is not None:
            return self.full_code

        return self.template.render({
            "app_path": self.path,
            "flags": self.flags,
            "includes": self.includes,
            "tunables": self.tunables,
            "deny_rules": self.deny_rules,
            "all_rules": self.all_rules,
            "rules": self.rules
        })

    def parse(self):
        text = read_apparmor_profile_by_name(self.name, directory=PROFILES_PATH)
        result = {
            "tunables": [],
            "abstractions": [],
            "rules": []
        }

        include_pattern = re.compile(r'^\s*#?include\s+<([^>]+)>')
        in_profile_body = False

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("profile") and stripped.endswith("{"):
                in_profile_body = True
                continue
            if stripped == "}":
                in_profile_body = False
                continue

            match = include_pattern.match(stripped)
            if match:
                include_target = match.group(1)
                if include_target.startswith("tunables/"):
                    result["tunables"].append(include_target)
                elif include_target.startswith("abstractions/"):
                    result["abstractions"].append(include_target)
                continue

            if in_profile_body:
                result["rules"].append(stripped.replace(',', ''))

        self.tunables = result['tunables']
        self.includes = result['abstractions']
        self.all_rules = result['rules']
        self.deny_rules = []
        self.rules = []

        return result

    def __deepcopy__(self, memo):
        copied = AppArmorProfile(
            name=copy.deepcopy(self.name, memo),
            path=copy.deepcopy(self.path, memo),
            flags=copy.deepcopy(self.flags, memo),
            includes=copy.deepcopy(self.includes, memo),
            tunables=copy.deepcopy(self.tunables, memo),
            deny_rules=copy.deepcopy(self.deny_rules, memo),
            disabled=copy.deepcopy(self.disabled, memo),
            mode=copy.deepcopy(self.mode, memo),
            rules=copy.deepcopy(self.rules, memo),
            full_code=copy.deepcopy(self.full_code, memo),
            all_rules=copy.deepcopy(self.all_rules, memo),
            template_name=self.template.name
        )
        return copied
