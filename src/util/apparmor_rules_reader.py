import os
import re
from typing import Any

from src.constants import PROFILES_PATH
from src.util.file_util import expand_apparmor_braces

CAP_FILE = "/usr/include/linux/capability.h"

capabilities_cache = None
tunables_cache = None
abstractions_cache = None


def get_capabilities() -> set[Any] | None:
    global capabilities_cache
    if capabilities_cache is not None:
        return capabilities_cache

    if not os.path.exists(CAP_FILE):
        print(f"File {CAP_FILE} not found.")
        return None

    capabilities = set()

    with open(CAP_FILE, "r") as f:
        for line in f:
            if line.startswith("#define CAP_"):
                parts = line.split()
                if len(parts) >= 2:
                    cap_name = parts[1]
                    if cap_name == "CAP_LAST_CAP":
                        continue
                    if cap_name.startswith("CAP_"):
                        cap_name = cap_name[4:]
                    cap_name = cap_name.lower()
                    capabilities.add(cap_name)

    capabilities_cache = capabilities
    return capabilities_cache


def get_tunables():
    global tunables_cache
    if tunables_cache is not None:
        return tunables_cache

    tunables_dir = f"{PROFILES_PATH}/tunables"
    tunables_files = {}

    if not os.path.isdir(tunables_dir):
        print(f"{tunables_dir} not found.")
        tunables_cache = {}
        return tunables_cache

    for entry in os.listdir(tunables_dir):
        full_path = os.path.join(tunables_dir, entry)
        if os.path.isfile(full_path):
            with open(full_path, "r") as f:
                tunables_files[entry] = f.read()

    tunables_cache = tunables_files
    return tunables_cache


def extract_tunables(tunables_dict: dict[str, str]) -> list[tuple[str, str]]:
    tunables = []

    for content in tunables_dict.values():
        matches = re.findall(r'(@\{\w+\})\s*=\s*([^\n#]+)', content)
        for var, paths in matches:
            for path in paths.split():
                tunables.append((var, path.strip()))
    return tunables


def get_abstractions():
    global abstractions_cache
    if abstractions_cache is not None:
        return abstractions_cache

    abstractions_dir = f"{PROFILES_PATH}/abstractions"
    abstractions_files = {}

    if not os.path.isdir(abstractions_dir):
        print(f"{abstractions_dir} not found.")
        abstractions_cache = {}
        return abstractions_cache

    for entry in os.listdir(abstractions_dir):
        full_path = os.path.join(abstractions_dir, entry)
        if os.path.isfile(full_path):
            with open(full_path, "r") as f:
                abstractions_files[entry] = f.read()

    abstractions_cache = abstractions_files
    return abstractions_cache


def normalize_abstractions_cache(raw_cache: dict[str, str]) -> dict[str, list[str]]:
    result = {}
    for name, content in raw_cache.items():
        result[name] = []
        for line in content.splitlines():
            line = line.strip().strip(',')
            if not line or line.startswith('#') or line.startswith('include'):
                continue

            if ' ' in line:
                path_part, perms = line.rsplit(' ', 1)
                expanded_paths = expand_apparmor_braces(path_part)
                for ep in expanded_paths:
                    result[name].append(f"{ep} {perms}")
            else:
                expanded_paths = expand_apparmor_braces(line)
                result[name].extend(expanded_paths)
    return result


def search_in_files(files_dict, query):
    results = {}
    for filename, content in files_dict.items():
        matching_lines = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            if query.lower() in line.lower():
                matching_lines.append((line_number, line))
        if matching_lines:
            results[filename] = matching_lines
    return results


def search_tunables(query):
    tunables = get_tunables()
    return search_in_files(tunables, query)


def search_abstractions(query):
    abstractions = get_abstractions()
    return search_in_files(abstractions, query)


def get_existing_capabilities():
    return [
        "chown",
        "dac_override",
        "dac_read_search",
        "fowner",
        "fsetid",
        "kill",
        "setgid",
        "setuid",
        "setpcap",
        "linux_immutable",
        "net_bind_service",
        "net_broadcast",
        "net_admin",
        "net_raw",
        "ipc_lock",
        "ipc_owner",
        "sys_module",
        "sys_rawio",
        "sys_chroot",
        "sys_ptrace",
        "sys_pacct",
        "sys_admin",
        "sys_boot",
        "sys_nice",
        "sys_resource",
        "sys_time",
        "sys_tty_config",
        "mknod",
        "lease",
        "audit_write",
        "audit_control",
        "setfcap",
        "mac_override",
        "mac_admin",
    ]
