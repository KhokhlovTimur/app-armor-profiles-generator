import logging
import os
import re
import tempfile

from src.constants import PROFILES_PATH
from src.model.apparmor_profile import AppArmorProfile
from src.util.command_executor_util import run_command


def profile_name_from_path(path: str) -> str:
    if path.startswith('/'):
        path = path[1:]
    return path.replace('/', '.')


def extract_profile_path(text: str) -> str | None:
    match = re.search(r'^\s*profile\s+(?:(\S+)\s+)?(/[^ \{]+)', text, re.MULTILINE)
    if match:
        return match.group(2)

    match = re.search(r'^\s*(/[^ \{]+)(?:\s+flags=\([^\)]+\))?\s*\{', text, re.MULTILINE)
    if match:
        return match.group(1)

    return None


def get_profile_path_from_file(file_path: str) -> str | None:
    try:
        result = run_command(['sudo', '-S', 'cat', PROFILES_PATH + "/" + file_path])

        if result.returncode != 0:
            print(f"{result.stderr}")
            return None

        return extract_profile_path(result.stdout)

    except Exception as e:
        print(f"{e}")
        return None


def extract_profile_body(profile_text: str) -> str:
    start_index = profile_text.find("{")
    end_index = profile_text.rfind("}")
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        return ""
    return profile_text[start_index + 1:end_index].strip()


def parse_profile_rules(profile_text: str) -> dict:
    body = extract_profile_body(profile_text)
    rules = {}

    for line in body.splitlines():
        line = line.strip()

        if line.startswith("include") or line.startswith("#include") or "include if exists" in line:
            rules[line] = ""
            continue
        elif line.startswith("#"):
            rules[line] = ""
            continue

        line = line.rstrip(',')
        parts = line.split()
        if len(parts) == 0:
            continue

        perms = ""
        path = ""
        if len(parts) == 1:
            path = parts[0]
        elif len(parts) >= 2:
            perms = parts[-1]
            path = " ".join(parts[:-1])

        rules[path] = perms

    return rules


def replace_profile_body_from_string(profile_as_string: str, new_body_text: str, tunables=None) -> str:
    match = re.search(r'(\{)(.*)(\})', profile_as_string, re.DOTALL)
    if not match:
        return ""

    header = profile_as_string[:match.start(1) + 1]
    footer = profile_as_string[match.end(3) - 1:]

    if tunables is not None:
        header = format_tunables(tunables)
        header += remove_tunables_from_profile(header)

    updated_profile = f"{header}\n\n{new_body_text.strip()}\n\n{footer}"

    return updated_profile


def format_tunables(tunables: list[str]) -> str:
    return "\n".join(sorted(set(tunables))) + "\n"


def remove_tunables_from_profile(profile_text: str) -> str:
    lines = profile_text.splitlines()
    filtered = [line for line in lines if not line.strip().startswith("#include <tunables/")]
    return "\n".join(filtered)


def replace_full_profile_from_file(profile_path: str, new_body_text: str):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(new_body_text)
        tmp_path = tmp.name

    try:
        return run_command([
            "sudo", "-S", "cp", tmp_path, profile_path
        ])
    finally:
        os.remove(tmp_path)


def replace_profile(profile_path, new_profile: AppArmorProfile):
    try:
        text_before = run_command(["sudo", "-S", "cat", profile_path])
        if text_before.returncode != 0:
            return
        profile_content = text_before.stdout
    except Exception as e:
        print(f"{e}")
        return


def replace_profile_body_from_file(profile_path: str, new_body_text: str, tunables=None):
    try:
        text_before = run_command(["sudo", "-S", "cat", profile_path])
        if text_before.returncode != 0:
            return
        profile_content = text_before.stdout
    except Exception as e:
        print(f"{e}")
        return

    updated_content = replace_profile_body_from_string(profile_content, extract_profile_body(new_body_text), tunables)
    if not updated_content:
        return

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(updated_content)
        tmp_path = tmp.name

    logging.info(f"Updating tmp profile body from {profile_path}")
    try:
        return run_command([
            "sudo", "-S", "cp", tmp_path, profile_path
        ])
    finally:
        os.remove(tmp_path)
        return text_before


def extract_profile_name(profile_str: str) -> str | None:
    match = re.search(r'^\s*profile\s+([^\s]+)', profile_str, re.MULTILINE)
    if match:
        name = match.group(1)
        if profile_str.startswith("/"):
            return name[1:]
        return name
    return None


def delete_profile(name: str):
    profile_path = PROFILES_PATH + "/" + name
    return run_command(["sudo", "-S", "rm", profile_path])

# def find_profile_name_by_binary_path(path: str) -> str:
#     res = run_command(["sudo", "-S", "grep", "-R", path, prof])
