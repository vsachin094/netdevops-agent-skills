#!/usr/bin/env python3
"""Small heuristic scanner for likely secrets in text files."""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    re.compile(r"(?i)(password|secret|token|private_key|snmp_community)\s*[:=]\s*['\"]?[^\s'\"]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
parser = argparse.ArgumentParser()
parser.add_argument("paths", nargs="+", type=Path)
args = parser.parse_args()
found = 0
for path in args.paths:
    if not path.is_file() or path.stat().st_size > 5_000_000:
        continue
    for line_no, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
        if any(pattern.search(line) for pattern in PATTERNS) and "vault_" not in line:
            print(f"{path}:{line_no}: possible secret", file=sys.stderr)
            found += 1
raise SystemExit(1 if found else 0)
