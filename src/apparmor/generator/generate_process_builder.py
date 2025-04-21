import subprocess
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal

from src.apparmor.apparmor_manager import read_apparmor_profile_by_name, get_logs_not_empty
from src.apparmor.apparmor_parser import validate_and_load_profile
from src.apparmor.generator.generator import AppArmorRuleGenerator
from src.constants import LOGS_TIME_PATTERN
from src.model.apparmor_profile import AppArmorProfile
from src.util.apparmor_rules_reader import normalize_abstractions_cache, get_abstractions
from src.util.apparmor_util import extract_profile_path, parse_apparmor_profile
from src.util.command_executor_util import launch_command_interactive
from src.util.file_util import join_project_root, save_logs


tmp_logs_path = join_project_root("data/", "logs")

class Generator(QObject):
    on_proc_terminated = pyqtSignal()


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
        launch_command_interactive(f"{self.profile.path}; exec bash", parent, lambda : analyze_profile_logs(self.profile.path, self.start_time))

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

    def update_profile_from_logs(self, profile: AppArmorProfile, is_from_file) -> AppArmorProfile:
        try:
            profile.parse()
            profile_text = profile.render()
            profile_path = extract_profile_path(profile_text)

            if not is_from_file:
                logs = get_logs_not_empty(profile.name, profile_path, tmp_logs_path)
                save_logs(logs, tmp_logs_path)
                if not logs:
                    print("Логи не найдены.")
                    return ""

            generator = AppArmorRuleGenerator()
            abstractions_raw = get_abstractions()
            abstractions_cache = normalize_abstractions_cache(abstractions_raw)

            tunables_new, abstractions_new, rules_new = generator.generate_rules(
                apply_tunables=True,
                apply_abstractions=True,
                abstractions_cache=abstractions_cache
            )

            existing_lines = set(line.strip() for line in profile_text.splitlines())

            tunables = [line for line in tunables_new if line.strip() and line.strip() not in existing_lines]
            abstractions = [line for line in abstractions_new if line.strip() and line.strip() not in existing_lines]
            rules = [line for line in rules_new if line.strip() and line.strip() not in existing_lines]

            print(
                f"[✓] Добавлено новых: tunables={len(tunables)}, abstractions={len(abstractions)}, rules={len(rules)}")

            profile.tunables.extend(tunables)
            profile.includes.extend(abstractions)
            profile.all_rules.extend(rules)

            # self.build_profile(profile.path, tunables, abstractions, rules)

            return profile

        except Exception as e:
            print(f"[Ошибка] Не удалось обновить профиль: {e}")
            return ""


def analyze_profile_logs(profile_path, start_time):
    try:
        subprocess.run(
            ["bash", join_project_root("scripts/", "redirect_logs.sh"), profile_path, start_time, tmp_logs_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    finally:
        # dialog.accept()
        pass
