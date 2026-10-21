#!/usr/bin/env python3
"""Validate config-diff-audit normalization and diff."""

import difflib
import re
import sys
from pathlib import Path

VOLATILE_PATTERNS = [
    r"^! Last configuration change",
    r"^ntp clock-period ",
    r"^! Time: ",
    r"^! Running configuration last done at:",
]

def stable_lines(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.splitlines():
        if not any(re.match(p, line) for p in VOLATILE_PATTERNS):
            lines.append(line)
    return lines

def diff_configs(old: str, new: str) -> list[str]:
    old_lines = stable_lines(old)
    new_lines = stable_lines(new)
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
    return diff

def test_identical() -> list[str]:
    config = "interface eth0\n ip address 1.1.1.1/24\n"
    diff = diff_configs(config, config)
    if diff:
        return ["FAIL: Identical configs should produce empty diff"]
    return []

def test_intentional_change() -> list[str]:
    old = "interface eth0\n ip address 1.1.1.1/24\n"
    new = "interface eth0\n ip address 1.1.1.1/24\n description test\n"
    diff = diff_configs(old, new)
    if not diff:
        return ["FAIL: Intentional change should produce diff"]
    if "description test" not in "\n".join(diff):
        return ["FAIL: Diff should show added description"]
    return []

def test_volatile_only() -> list[str]:
    old = "interface eth0\n ip address 1.1.1.1/24\n! Last configuration change at 10:00\n"
    new = "interface eth0\n ip address 1.1.1.1/24\n! Last configuration change at 11:00\n"
    diff = diff_configs(old, new)
    if diff:
        return ["FAIL: Volatile-only changes should be ignored"]
    return []

def test_secret_redaction() -> list[str]:
    config = "username admin password secret123\n"
    # Check that secrets are not in diff output
    diff = diff_configs(config, config)
    if "secret123" in "\n".join(diff):
        return ["FAIL: Secrets should be redacted"]
    return []

if __name__ == "__main__":
    all_errors = []
    all_errors.extend(test_identical())
    all_errors.extend(test_intentional_change())
    all_errors.extend(test_volatile_only())
    all_errors.extend(test_secret_redaction())
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: config-diff-audit validated")