import datetime
import fnmatch
import os.path
import re

from src.constants import PROJECT_ROOT, PROFILES_PATH


def join_project_root(*args):
    return os.path.join(PROJECT_ROOT, *args)


def load_stylesheet(file_name, elem):
    __path = join_project_root("resources", "styles/")
    with open(__path + file_name, "r") as file:
        elem.setStyleSheet(file.read())


def load_stylesheet_buttons(elem):
    load_stylesheet("buttons.qss", elem)


def expand_apparmor_braces(pattern: str) -> list[str]:
    brace_pattern = re.compile(r'\{([^}]+)\}')
    match = brace_pattern.search(pattern)

    if not match:
        return [pattern]

    options = match.group(1).split(',')
    prefix = pattern[:match.start()]
    suffix = pattern[match.end():]

    results = []
    for opt in options:
        expanded = prefix + opt + suffix
        results.extend(expand_apparmor_braces(expanded))

    return results


def match_with_limited_wildcards(rule_path: str, pattern: str, max_mismatches: int = 1) -> bool:
    rule_segments = rule_path.strip("/").split("/")
    pattern_segments = pattern.strip("/").split("/")

    mismatches = 0
    for i in range(min(len(rule_segments), len(pattern_segments))):
        if not fnmatch.fnmatch(rule_segments[i], pattern_segments[i]):
            mismatches += 1
            if mismatches > max_mismatches:
                return False

    mismatches += abs(len(rule_segments) - len(pattern_segments))
    return mismatches <= max_mismatches


def is_too_generic_pattern(pattern: str) -> bool:
    return pattern.startswith("/**")


def get_profile_file_timestamp(profile_name: str) -> dict:
    result = {}
    profile_path = "/etc/apparmor.d/" + profile_name
    try:
        mtime = os.path.getmtime(profile_path)
        result["modified"] = datetime.datetime.fromtimestamp(mtime)

        if hasattr(os, "stat"):
            stat = os.stat(profile_path)
            if hasattr(stat, "st_birthtime"):
                result["created"] = datetime.datetime.fromtimestamp(stat.st_birthtime)
            elif hasattr(stat, "st_ctime"):
                result["created"] = datetime.datetime.fromtimestamp(stat.st_ctime)

    except FileNotFoundError:
        result["error"] = "Файл не найден"
    except Exception as e:
        result["error"] = str(e)

    return result


def get_profile_created_or_modified_date(profile_name: str):
    res = get_profile_file_timestamp(profile_name=profile_name)
    if res["modified"] is not None:
        return res["modified"].strftime("%Y-%m-%d %H:%M:%S")
    else:
        return res["created"].strftime("%Y-%m-%d %H:%M:%S")


def is_binary_executable(b_path: str) -> bool:
    if not os.path.isfile(b_path):
        return False

    if not os.access(b_path, os.X_OK):
        return False

    return True


def save_logs(logs: list[str], path: str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))
    except Exception as e:
        print(f"{path}: {e}")
