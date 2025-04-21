import fnmatch
import os
import re

import re
import subprocess

from src.apparmor.generator.parsers import UserNsParser, CapabilityParser, SignalParser, PtraceParser, PivotRootParser, \
    MountParser, DbusParser, NetworkParser, ExecParser
from src.util.apparmor_rules_reader import abstractions_cache, get_abstractions, get_tunables, extract_tunables, \
    normalize_abstractions_cache
from src.util.file_util import join_project_root, expand_apparmor_braces


class AppArmorRuleGenerator:
    def __init__(self):
        self.rule_classes = [
            CapabilityParser(), SignalParser(), PtraceParser(), PivotRootParser(), MountParser(),
            UserNsParser(),  DbusParser(), NetworkParser(), ExecParser()
        ]
        self.file_rules = {}

    def generate_rules(
            self,
            log_path: str = join_project_root("data/", "logs"),
            apply_tunables: bool = True,
            apply_abstractions: bool = True,
            abstractions_cache: dict[str, list[str]] = None
    ) -> tuple[list[str], list[str], list[str]]:
        rules = set()
        with open(log_path, "r") as f:
            lines = f.readlines()

        for line in lines:
            matched = False
            for rule_class in self.rule_classes:
                if rule_class.match(line):
                    result = rule_class.generate(line)
                    if isinstance(result, tuple):  # exec
                        path, mode = result
                        perms = self.file_rules.setdefault(path, '')
                        for p in mode:
                            if p not in perms:
                                perms += p
                        self.file_rules[path] = perms
                        matched = True
                        break
                    elif isinstance(result, str):
                        rules.add(result)
                        matched = True
                        break

            if not matched:
                self._process_file_access(line)

        perm_order = ['r', 'w', 'm', 'i', 'x', 'k']
        for path, perms in sorted(self.file_rules.items()):
            ordered = ''.join(p for p in perm_order if p in perms)
            rules.add(f"{path} {ordered}")

        rules = sorted(rules)

        tunables_includes = []
        tunables_dict = get_tunables()
        flat_tunables = extract_tunables(tunables_dict)

        if apply_tunables:
            rules = self.apply_tunables(rules, flat_tunables)

            used_vars = set()
            for rule in rules:
                used_vars.update(re.findall(r'@\{\w+\}', rule))

            for tun_name, content in tunables_dict.items():
                for var in used_vars:
                    if var in content:
                        tunables_includes.append(f"tunables/{tun_name}")
                        break

        abstractions_includes = []
        used_abstraction_names = set()
        if apply_abstractions and abstractions_cache:
            rules = self.replace_with_abstractions(rules, used_abstraction_names)
            for rule in rules[:]:
                if rule.startswith("abstractions/"):
                    abstractions_includes.append(rule)
                    used_abstraction_names.add(rule.replace("abstractions/", ""))
                    rules.remove(rule)

        tunables_from_abstractions = self.find_all_used_tunables(get_abstractions(), tunables_dict, used_abstraction_names)
        tunables_includes.extend(tunables_from_abstractions)

        return sorted(set(tunables_includes)), sorted(set(abstractions_includes)), sorted(rules)

    def find_all_used_tunables(self, abstractions_dict: dict[str, str], tunables_dict: dict[str, str], used_abstractions: set[str]) -> set[str]:
        include_pattern = re.compile(r'^\s*include\s+<abstractions/([^>]+)>', re.MULTILINE)
        var_pattern = re.compile(r'@\{\w+\}')

        visited = set()
        tunables_used = set()
        queue = list(used_abstractions)

        while queue:
            name = queue.pop()
            if name in visited:
                continue
            visited.add(name)

            content = abstractions_dict.get(name, "")
            tunables_used.update(var_pattern.findall(content))

            includes = include_pattern.findall(content)
            for inc in includes:
                if inc not in visited:
                    queue.append(inc)

        tunables_includes = set()
        for tun_name, content in tunables_dict.items():
            for var in tunables_used:
                if var in content:
                    tunables_includes.add(f"tunables/{tun_name}")
                    break

        return tunables_includes

    def _process_file_access(self, line):
        name_re = re.compile(r'name="([^"]+)"')
        mask_re = re.compile(r'requested_mask="([^"]+)"')

        name_match = name_re.search(line)
        if not name_match:
            return
        path = name_match.group(1)
        if not path:
            return

        perms = self.file_rules.setdefault(path, '')
        mask_match = mask_re.search(line)
        if mask_match:
            mask = mask_match.group(1)
            if 'r' in mask and 'r' not in perms:
                perms = 'r' + perms
            if any(x in mask for x in ['w', 'a', 'c', 'u']) and 'w' not in perms:
                perms += 'w'
            if 'm' in mask and 'm' not in perms:
                perms += 'm'
        else:
            if 'r' not in perms:
                perms = 'r' + perms
        self.file_rules[path] = perms


    def normalize_rule(self, rule: str) -> tuple[str, str]:
        rule = rule.strip().strip(',')
        if not rule or rule.startswith('#'):
            return '', ''
        if ' ' not in rule:
            return rule, ''
        parts = rule.rsplit(' ', 1)
        if len(parts) != 2:
            return '', ''
        path, perms = parts
        perms = ''.join(sorted(perms.strip(',')))
        return path.strip(), perms

    def pattern_matches_rule(self, rule_path: str, rule_perms: str, pattern_path: str, pattern_perms: str) -> bool:
        if rule_path == pattern_path:
            return all(p in pattern_perms for p in rule_perms)

        if fnmatch.fnmatch(rule_path, pattern_path):
            return all(p in pattern_perms for p in rule_perms)

        return False

    def replace_with_abstractions(
            self,
            rules: list[str],
            used_abstraction_names: set[str]
    ) -> list[str]:
        used_includes = set()
        remaining_rules = set(rules)

        abstraction_dir = "/etc/apparmor.d/abstractions"
        grep_targets = list(remaining_rules)

        for rule in grep_targets:
            rule_path, rule_perms = self.normalize_rule(rule)
            if not rule_path:
                continue
            try:
                result = subprocess.run(
                    ['grep', '-r', rule_path, abstraction_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
            except Exception:
                continue

            matches = result.stdout.strip().splitlines()
            for match in matches:
                if ":" not in match:
                    continue
                filepath, line = match.split(":", 1)
                line = line.strip().strip(',')

                if not line or line.startswith("#"):
                    continue

                line_path, line_perms = self.normalize_rule(line)

                if line_path == rule_path and line_perms == rule_perms:
                    abstraction_name = os.path.basename(filepath)
                    include_path = f"abstractions/{abstraction_name}"
                    used_includes.add(include_path)
                    used_abstraction_names.add(abstraction_name)
                    remaining_rules.remove(rule)
                    break

        return sorted(used_includes) + sorted(remaining_rules)

    def apply_tunables(self, rules: list[str], tunables_cache: list[tuple[str, str]]) -> list[str]:
        updated = []
        for rule in rules:
            for var, path in tunables_cache:
                if path.endswith("/") and path in rule:
                    rule = rule.replace(path, var + "/")
                elif path in rule:
                    rule = rule.replace(path, var)
            updated.append(rule)
        return updated

    def merge_with_existing_profile(self, profile_path: str, new_rules: list[str]) -> list[str]:
        try:
            with open(profile_path, "r") as f:
                existing_lines = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            existing_lines = []

        existing_rules = set(line.strip(',') for line in existing_lines if line and not line.startswith('#'))

        result = existing_lines.copy()
        for rule in new_rules:
            clean_rule = rule.strip(',')
            if clean_rule not in existing_rules:
                result.append(rule)
                existing_rules.add(clean_rule)
        return result



gen = AppArmorRuleGenerator()
abstractions_raw = get_abstractions()
abstractions_cache_1 = normalize_abstractions_cache(abstractions_raw)

includes, abstractions, rules = gen.generate_rules(
    apply_tunables=True,
    apply_abstractions=True,
    abstractions_cache=abstractions_cache_1
)

print("Tunables:")
print("\n".join(includes))

print("\nAbstractions:")
print("\n".join(abstractions))

print("\nRules:")
print("\n".join(rules))
