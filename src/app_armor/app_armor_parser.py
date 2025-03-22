import os
import re
import subprocess
import tempfile

from src.util.command_executor_util import run_command


def validate_profile(profile_string: str):
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write(profile_string)
            temp_path = tmp.name

        result = run_command([
            "sudo", "-S", "apparmor_parser", "-r", temp_path
        ])

        os.remove(temp_path)
        return result
    except Exception as e:
        print(f"Ошибка при проверке профиля: {e}")
        return subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr=str(e))

def save_and_add_profile(profile_string: str, profile_filename: str):
    try:
        filepath = f"/etc/apparmor.d/{profile_filename}"

        temp_profile_path = os.path.join(tempfile.gettempdir(), profile_filename)
        with open(temp_profile_path, "w") as f:
            f.write(profile_string)

        copy_result = run_command([
            "sudo", "-S", "cp", temp_profile_path, filepath
        ])

        if copy_result.returncode != 0:
            return copy_result

        result = run_command([
            "sudo", "-S", "apparmor_parser", "-r", filepath
        ])

        return result
    except Exception as e:
        print(f"Ошибка при сохранении/добавлении: {e}")
        return subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr=str(e))

def filter_stderr(stderr: str) -> str:
    stderr = stderr.strip()
    stderr = re.sub(r'^\[sudo\] пароль для .*?:\s*', '', stderr)
    return stderr

def validate_and_load_profile(profile_string: str, profile_filename: str):
    validation_result = validate_profile(profile_string)
    if validation_result.returncode != 0:
        print(filter_stderr(validation_result.stderr))
        return validation_result

    result = save_and_add_profile(profile_string, profile_filename)
    if result.returncode == 0:
        print("Профиль успешно добавлен.")
    else:
        print(filter_stderr(result.stderr))
    return result

def edit_profile(profile_string: str, profile_filename: str):
    try:
        filepath = f"/etc/apparmor.d/{profile_filename}"

        temp_profile_path = os.path.join(tempfile.gettempdir(), profile_filename)
        with open(temp_profile_path, "w") as f:
            f.write(profile_string)

        copy_result = run_command([
            "sudo", "-S", "cp", temp_profile_path, filepath
        ])

        if copy_result.returncode != 0:
            return copy_result

        reload_result = run_command([
            "sudo", "-S", "apparmor_parser", "-r", filepath
        ])

        return reload_result

    except Exception as e:
        print(f"Ошибка при редактировании профиля: {e}")
        return subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr=str(e))