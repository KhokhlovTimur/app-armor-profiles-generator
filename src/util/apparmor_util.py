import os
import re
import tempfile

from src.util.command_executor_util import run_command


def extract_profile_path(text: str) -> str | None:
    match = re.search(r'^\s*profile\s+(?:(\S+)\s+)?(/[^ \{]+)', text, re.MULTILINE)
    if match:
        return match.group(2)

    match = re.search(r'^\s*(/[^ \{]+)(?:\s+flags=\([^\)]+\))?\s*\{', text, re.MULTILINE)
    if match:
        return match.group(1)

    return None

def extract_profile_body(profile_text: str) -> str:
    start_index = profile_text.find("{")
    if start_index == -1:
        return ""

    brace_count = 1
    index = start_index + 1

    while index < len(profile_text):
        if profile_text[index] == '{':
            brace_count += 1
        elif profile_text[index] == '}':
            brace_count -= 1
            if brace_count == 0:
                return profile_text[start_index + 1:index].strip()
        index += 1

    return ""

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

def replace_profile_body_from_string(profile_as_string: str, new_body_text: str) -> str:
    match = re.search(r'(\{)(.*)(\})', profile_as_string, re.DOTALL)
    if not match:
        return ""

    header = profile_as_string[:match.start(1) + 1]
    footer = profile_as_string[match.end(3) - 1:]

    updated_profile = f"{header}\n\n{new_body_text.strip()}\n\n{footer}"

    return updated_profile


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


def replace_profile_body_from_file(profile_path: str, new_body_text: str):
    try:
        text_before = run_command(["sudo", "-S", "cat", profile_path])
        if text_before.returncode != 0:
            return
        profile_content = text_before.stdout
    except Exception as e:
        print(f"{e}")
        return

    updated_content = replace_profile_body_from_string(profile_content, extract_profile_body(new_body_text))
    if not updated_content:
        return

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(updated_content)
        tmp_path = tmp.name

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
        return match.group(1)
    return None

