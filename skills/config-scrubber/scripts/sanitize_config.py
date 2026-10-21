#!/usr/bin/env python3
"""Deterministically redact common network secrets from text."""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    (re.compile(r"(?i)(password|secret|community|pre-shared-key)\s+(\S+)"), r"\1 <REDACTED>"),
    (re.compile(r"(?i)(username\s+\S+\s+password)\s+(\S+)"), r"\1 <REDACTED>"),
    (re.compile(r"-----BEGIN [^-]+PRIVATE KEY-----.*?-----END [^-]+PRIVATE KEY-----", re.S), "<PRIVATE_KEY_REDACTED>"),
]
parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
try:
    text = args.input.read_text(encoding="utf-8")
    counts = 0
    for pattern, replacement in PATTERNS:
        text, count = pattern.subn(replacement, text)
        counts += count
    args.output.write_text(text, encoding="utf-8")
except OSError as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    raise SystemExit(2)
print(f"PASS: scrubbed {counts} sensitive matches")
