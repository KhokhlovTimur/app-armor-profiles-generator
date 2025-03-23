import os
import subprocess
from datetime import timedelta, datetime

from src.util.command_executor_util import run_command


class AppArmorManager:
    def __init__(self):
        pass

    def check_status(self):
        return run_command(["sudo", "aa-status"])

    def reload_apparmor(self):
        return run_command(["sudo", "systemctl", "reload", "apparmor"])

    def check_service_status(self):
        return run_command(["sudo", "systemctl", "status", "apparmor"])

    def read_apparmor_profile_by_name( self, profile_name, directory="/etc/apparmor.d"):
        for filename in os.listdir(directory):
            if filename == profile_name or filename.replace('/', '.') == profile_name:
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, 'r') as f:
                        return f.read()
                except Exception as e:
                    print(f"Ошибка при чтении файла: {e}")
                    return None
        return None

    def remove_profile(self, profile_name):
        return run_command(["sudo", "apparmor_parser", "-R", f"/etc/apparmor.d/{profile_name}"])

    def list_profiles(self):
        return run_command(["sudo", "ls", "/etc/apparmor.d/"])

    def get_profiles_from_apparmor_d(self, directory: str = "/etc/apparmor.d") -> list:
        try:
            profiles = []
            result = run_command(["sudo", "-S", "aa-status"])
            if result.returncode != 0:
                raise Exception("Не удалось получить статус AppArmor")

            lines = result.stdout.splitlines()
            mode_map = {}
            current_mode = None
            modes = {
                "enforce": "enforce mode",
                "complain": "complain mode",
                "kill": "kill mode",
                "unconfined": "unconfined mode",
                "prompt": "prompt mode"
            }

            for line in lines:
                for mode_key, mode_val in modes.items():
                    if mode_val in line:
                        current_mode = mode_key
                        continue

                if current_mode and line.strip():
                    mode_map[line.strip()] = current_mode

            disable_dir = os.path.join(directory, "disable")
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if not os.path.isfile(filepath):
                    continue

                disabled = False
                disable_link_path = os.path.join(disable_dir, filename)
                if os.path.islink(disable_link_path):
                    target = os.readlink(disable_link_path)
                    if target == f"../{filename}":
                        disabled = True

                profile_mode = mode_map.get(filename, "disabled")
                profiles.append({
                    'name': filename,
                    'mode': profile_mode,
                    'path': filepath,
                    'disabled': profile_mode == 'disabled'
                })

            return profiles
        except Exception as e:
            print(f"Ошибка при получении списка профилей: {e}")
            return []

    def get_profile_mode_by_name(self, profile_name: str) -> str:
        try:
            result = run_command(["sudo", "-S", "aa-status"])
            if result.returncode != 0:
                return "unknown"

            lines = result.stdout.splitlines()
            current_mode = None
            modes = {
                "enforce": "enforce mode",
                "complain": "complain mode",
                "kill": "kill mode",
                "unconfined": "unconfined mode",
                "prompt": "prompt mode"
            }

            for line in lines:
                for mode_key, mode_val in modes.items():
                    if mode_val in line:
                        current_mode = mode_key
                        continue

                if current_mode and line.strip() == profile_name:
                    return current_mode

            return "disabled"
        except Exception as e:
            print(f"Ошибка при получении режима профиля '{profile_name}': {e}")
            return "error"

    def get_logs(self, profile_name: str) -> list:
        logs = self._get_logs_from("apparmor", profile_name)
        logs.extend(self._get_logs_from("apparmor_parser", profile_name))
        return logs if len(logs) > 0 else ['Not found']

    def _get_logs_from(self, _from, profile_name):
        since = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")

        result = run_command([
            "journalctl", "-k", "--since", since
        ])

        if result.returncode != 0:
            return ["Ошибка при получении логов"]

        logs = result.stdout.strip().splitlines()

        filtered_logs = [
            line for line in logs
            if f'name="{profile_name}"' in line and _from.lower() in line.lower()
        ]
        # if result_apparmor.returncode == 0:
        #     logs = result_apparmor.stdout.strip().splitlines()
        #     profile_key = f"profile={profile_name}"
        #     filtered_logs = [log for log in logs if profile_key in log]
        # else:
        #     filtered_logs.append("Ошибка при получении логов AppArmor.")

        return filtered_logs

    def change_profile_mode(self, profile_name: str, mode: str):
        try:
            if mode not in ["enforce", "complain", "disable", "enable"]:
                raise ValueError("Bad Request: 'enforce', 'complain' или 'disable'.")

            cmd_map = {
                "enforce": ["sudo", "-S", "aa-enforce", profile_name],
                "complain": ["sudo", "-S", "aa-complain", profile_name],
                "disable": ["sudo", "-S", "aa-disable", profile_name],
                "enable": ["sudo", "-S", "aa-complain", profile_name]
            }

            result = run_command(cmd_map[mode])
            return result

        except Exception as e:
            print(f"Ошибка при смене режима: {e}")
            return None

    def is_profile_disabled(self, profile_name: str, base_dir: str = "/etc/apparmor.d") -> bool:
        result = run_command(["sudo", "aa-status"])
        if result.returncode != 0:
            return False

        loaded_profiles = result.stdout.splitlines()
        for line in loaded_profiles:
            if profile_name in line.strip():
                return True

        return False

