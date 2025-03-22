import os
from datetime import timedelta, datetime

from src.util.command_executor_util import run_command


class AppArmorManager:
    def __init__(self):
        pass

    def check_status(self):
        return run_command(["sudo", "aa-status"])

    def enforce_profile(self, profile_name):
        return run_command(["sudo", "aa-enforce", profile_name])

    def complain_profile(self, profile_name):
        return run_command(["sudo", "aa-complain", profile_name])

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

            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if not os.path.isfile(filepath):
                    continue

                profile_mode = mode_map.get(filename, "not loaded")
                profiles.append({
                    'name': filename,
                    'mode': profile_mode,
                    'path': filepath
                })

            return profiles
        except Exception as e:
            print(f"Ошибка при получении списка профилей: {e}")
            return []

    # def get_profile_logs(self, profile_name: str) -> list:
    #     try:
    #         def fetch():
    #             since_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    #             result = run_command([
    #                 "journalctl", "-q", "--no-pager",
    #                 "--since", since_time,
    #                 "--grep", profile_name
    #             ])
    #             if result.returncode != 0:
    #                 return ["Ошибка при получении логов"]
    #             logs = result.stdout.strip().splitlines()
    #             return logs if logs else ["Логи не найдены"]
    #
    #         return AppArmorWorker().exec_async(fetch)
    #     except Exception as e:
    #         return [f"Ошибка: {e}"]

