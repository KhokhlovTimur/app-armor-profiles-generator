import logging
import os
import re
import subprocess
import tempfile

from src.apparmor.apparmor_manager import reload_apparmor
from src.constants import PROFILES_PATH
from src.util.apparmor_util import replace_profile_body_from_file, replace_full_profile_from_file
from src.util.command_executor_util import run_command
from src.util.file_util import join_project_root

TMP_PROFILE_NAME = "tmp_profile"

def validate_profile(profile_string: str):
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write(profile_string)
            temp_path = tmp.name

        result = run_command([
            "sudo", "-S", "apparmor_parser", "-K", '-T', temp_path
        ])

        os.remove(temp_path)
        return result
    except Exception as e:
        print(f"Ошибка при проверке профиля: {e}")
        return subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr=str(e))

def save_and_add_profile(profile_string: str, profile_filename: str):
    try:
        profile_filename = profile_filename.lstrip("/").replace("/", ".")
        filepath = f"{PROFILES_PATH}/{profile_filename}"
        tmp_filepath = f"{PROFILES_PATH}/{TMP_PROFILE_NAME}"
        text_before = replace_profile_body_from_file(tmp_filepath, profile_string).stdout

        parser_result = run_command([
            "sudo", "-S", "apparmor_parser", "-r", tmp_filepath
        ])

        logging.info(f"Updating tmp profile ")

        if parser_result.returncode != 0:
            filepath = f"{PROFILES_PATH}/{TMP_PROFILE_NAME}"
            run_command([
                "sudo", "-S", "cp", join_project_root("resources", "tmp_profile"), filepath
            ])
            return parser_result

        logging.info(f"Copying body from tmp to {filepath}")
        process = subprocess.run(
            ["sudo", "tee", filepath],
            input=profile_string.encode(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )

        if process.returncode != 0:
            print("Ошибка:", process.stderr.decode())
        else:
            print(f"Файл записан: {filepath}")

        logging.info(f"Adding profile {filepath} to kernel...")
        result = run_command([
            "sudo", "-S", "apparmor_parser", "-a", filepath
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
    result = save_and_add_profile(profile_string, profile_filename)
    if result.returncode == 0:
        logging.info(f"Profile {profile_filename} is loaded.")
        print("Профиль успешно добавлен.")
    else:
        logging.error(f"Profile {profile_filename} is not loaded: {filter_stderr(result.stderr)}")
        print(filter_stderr(result.stderr))
    return result

def edit_profile_body_and_check(profile_string: str, profile_filename: str):
    try:
        tmp_filepath = f"{PROFILES_PATH}/{TMP_PROFILE_NAME}"
        filepath = f"{PROFILES_PATH}/{profile_filename}"

        text_before = replace_profile_body_from_file(tmp_filepath, profile_string).stdout

        parser_result = run_command([
            "sudo", "-S", "apparmor_parser", "-r", tmp_filepath
        ])

        if parser_result.returncode != 0:
            filepath = f"{PROFILES_PATH}/{TMP_PROFILE_NAME}"
            run_command([
                "sudo", "-S", "cp", join_project_root("resources", "tmp_profile"), filepath
            ])
            return parser_result

        if tmp_filepath == filepath:
            reload_result = reload_apparmor()
            return reload_result

        copy_result = replace_full_profile_from_file(filepath, profile_string)
        if copy_result.returncode != 0:
            return copy_result

        reload_result = reload_apparmor()

        return reload_result

    except Exception as e:
        print(f"Error editing profile: {e}")
        return subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr=str(e))

def load_tmp_profile():
    filepath = f"{PROFILES_PATH}/{TMP_PROFILE_NAME}"
    result = run_command(["sudo", "-S", "cp", join_project_root("resources", "tmp_profile"), filepath])

    result = run_command([
        "sudo", "-S", "apparmor_parser", "-r", filepath
    ])
    reload_apparmor()
    return

