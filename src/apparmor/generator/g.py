import subprocess
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal

from src.apparmor.apparmor_parser import validate_and_load_profile
from src.apparmor.generator.generator import AppArmorRuleGenerator
from src.constants import LOGS_TIME_PATTERN
from src.model.apparmor_profile import AppArmorProfile
from src.util.apparmor_rules_reader import normalize_abstractions_cache, get_abstractions
from src.util.command_executor_util import launch_command_interactive
from src.util.file_util import join_project_root


class Generator(QObject):
    on_proc_terminated = pyqtSignal()

    tmp_logs_path = join_project_root("data/", "logs")

    def __init__(self):
        super().__init__()
        self.profile = None

    def start_generate(self, bin_path):
        profile = AppArmorProfile(path=bin_path, includes=["abstractions/base"])
        self.profile = profile
        profile_string = profile.render()
        return validate_and_load_profile(profile_string, profile.path)

    def exec_app(self, parent):
        print(f'exec {self.profile.path}')
        self.parent = parent
        self.start_time = datetime.now().strftime(LOGS_TIME_PATTERN)
        launch_command_interactive(f"{self.profile.path}; exec bash", parent, self._analyze_profile_logs)

    def _analyze_profile_logs(self):
        try:
            print("logs")
            subprocess.run(
                ["bash", join_project_root("scripts/", "redirect_logs.sh"), self.profile.path, self.start_time, self.tmp_logs_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        finally:
            # dialog.accept()
            pass

    def run_generate(self):
        try:
            gen = AppArmorRuleGenerator()
            abstractions_raw = get_abstractions()
            abstractions_cache_1 = normalize_abstractions_cache(abstractions_raw)

            includes, abstractions, rules = gen.generate_rules(
                apply_tunables=True,
                apply_abstractions=True,
                abstractions_cache=abstractions_cache_1
            )

            return includes, abstractions, rules

        except Exception as e:
            print(f"Error in profile {self.profile.path} generating: {e}")

    def build_profile(self, path: str, tunables: list[str], abstractions: list[str], rules: list[str]) -> str:
        lines = []

        lines.extend(tunables)

        lines.append("")
        lines.append(f"profile {path} {{")

        for abs_line in abstractions:
            lines.append(f"    {abs_line}")

        lines.append("")
        for rule in rules:
            lines.append(f"    {rule}")

        lines.append("}")
        return "\n".join(lines)
