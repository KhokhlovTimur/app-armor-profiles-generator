import os
import subprocess
from datetime import timedelta, datetime

from src.constants import PROFILES_PATH, LOGS_TIME_PATTERN
from src.util.command_executor_util import run_command
from src.util.file_util import get_profile_file_timestamp, get_profile_created_or_modified_date


def check_status():
    return run_command(["sudo", "aa-status"])


def reload_apparmor():
    return run_command(["sudo", "systemctl", "reload", "apparmor"])


def check_service_status():
    return run_command(["sudo", "systemctl", "status", "apparmor"])


def read_apparmor_profile_by_name(profile_name, directory=PROFILES_PATH):
    for filename in os.listdir(directory):
        base_name = filename.rstrip(".profile")
        if filename == profile_name or base_name == profile_name or filename.replace('/', '.') == profile_name:
            file_path = os.path.join(directory, filename)
            try:
                # Пробуем обычное открытие
                with open(file_path, 'r') as f:
                    return f.read()
            except PermissionError:
                print(f"[!] Нет доступа к {file_path}, пробуем через sudo...")

                try:
                    # Пробуем прочитать через sudo
                    output = subprocess.check_output(["sudo", "cat", file_path], text=True)
                    return output
                except Exception as e:
                    print(f"Ошибка при чтении с правами sudo: {e}")
                    return None
            except Exception as e:
                print(f"Ошибка при чтении файла: {e}")
                return None
    return None


def remove_profile(profile_name):
    return run_command(["sudo", "apparmor_parser", "-R", f"{PROFILES_PATH}/{profile_name}"])


def list_profiles():
    return run_command(["sudo", "ls", PROFILES_PATH])


def get_profiles_from_apparmor_d(directory: str = PROFILES_PATH) -> list:
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

            profile_mode = mode_map.get(filename, "disabled")
            if profile_mode == "disabled" and filename is not None:
                profile_mode = mode_map.get("/" + filename.replace(".", "/"), "disabled")

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


def get_profile_mode_by_name(profile_name: str) -> str:
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

            if current_mode and line.strip() == profile_name or (line.strip() == "/" + profile_name.replace(".", "/")):
                return current_mode

        return "disabled"
    except Exception as e:
        print(f"Ошибка при получении режима профиля '{profile_name}': {e}")
        return "error"


def get_logs_not_empty(profile_name: str, profile_path=None, status=None) -> list:
    logs = get_logs_from(_from="apparmor", profile_name=profile_name, profile_path=profile_path, status=status,
                              since=get_profile_created_or_modified_date(profile_name))
    return logs if len(logs) > 0 else ['Not found']


def get_logs_from(_from="apparmor", profile_name=None, profile_path=None, status=None,
                  since=(datetime.now() - timedelta(hours=1)).strftime(LOGS_TIME_PATTERN)):
    result = run_command([
        "journalctl", "-g", profile_name, "--since", since, "--no-pager"
    ])

    if result.returncode != 0:
        return ["Ошибка при получении логов"]

    logs = result.stdout.strip().splitlines()

    filtered_logs = []
    for line in logs:
        if f'profile="{profile_name}"' in line or f'profile="{profile_path}"' in line:
            if (status is not None and f'apparmor={status}' in line) or status is None:
                if _from.lower() in line.lower():
                    filtered_logs.append(line)

    return filtered_logs

def change_profile_mode(profile_name: str, mode: str):
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


def is_profile_disabled(profile_name: str, base_dir: str = PROFILES_PATH) -> bool:
    result = run_command(["sudo", "aa-status"])
    if result.returncode != 0:
        return False

    loaded_profiles = result.stdout.splitlines()
    for line in loaded_profiles:
        if profile_name in line.strip():
            return True

    return False
