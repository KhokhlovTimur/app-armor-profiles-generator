import fnmatch
import re

import re

from src.apparmor.generator.parsers import UserNsParser, CapabilityParser, SignalParser, PtraceParser, PivotRootParser, \
    MountParser, DbusParser, NetworkParser, ExecParser
from src.util.apparmor_rules_reader import abstractions_cache, get_abstractions, get_tunables, extract_tunables, \
    normalize_abstractions_cache
from src.util.file_util import join_project_root


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
            abstractions_cache: dict[str, tuple[str]] = None
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
            rules.add(f"{path} {ordered},")

        rules = sorted(rules)

        tunables_includes = []
        if apply_tunables:
            tunables_dict = get_tunables()
            flat_tunables = extract_tunables(tunables_dict)
            rules = self.apply_tunables(rules, flat_tunables)

            used_vars = set()
            for rule in rules:
                used_vars.update(re.findall(r'@\{\w+\}', rule))

            for tun_name, content in tunables_dict.items():
                for var in used_vars:
                    if var in content:
                        tunables_includes.append(f"#include <tunables/{tun_name}>")
                        break

        abstractions_includes = []
        if apply_abstractions and abstractions_cache:
            rules = self.replace_with_abstractions(rules, abstractions_cache)
            for rule in rules[:]:
                if rule.startswith("#include <abstractions/"):
                    abstractions_includes.append(rule)
                    rules.remove(rule)

        return sorted(set(tunables_includes)), sorted(set(abstractions_includes)), sorted(rules)

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
        path_match = fnmatch.fnmatch(rule_path, pattern_path)
        perms_match = all(p in pattern_perms for p in rule_perms)
        return path_match and perms_match

    def replace_with_abstractions(self, rules: list[str], abstractions_cache: dict[str, list[str]]) -> list[str]:
        used_includes = set()
        remaining_rules = set(rules)

        for abstraction_name, patterns in abstractions_cache.items():
            matched_rules = set()

            for pattern in patterns:
                pattern_path, pattern_perms = self.normalize_rule(pattern)
                for rule in remaining_rules:
                    rule_path, rule_perms = self.normalize_rule(rule)
                    if self.pattern_matches_rule(rule_path, rule_perms, pattern_path, pattern_perms):
                        matched_rules.add(rule)

            if matched_rules:
                used_includes.add(f"#include <abstractions/{abstraction_name}>")
                remaining_rules -= matched_rules

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
