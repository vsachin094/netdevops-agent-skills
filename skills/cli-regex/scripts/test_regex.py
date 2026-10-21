#!/usr/bin/env python3
"""Run a named-group regex against a fixture and compare JSON records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ANSI = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
PAGER = re.compile(r"(?:\x08+|--More--|\x1b\[K)")


def normalize_cli(text: str) -> str:
    text = ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    text = PAGER.sub("", text)
    return "\n".join(line.rstrip() for line in text.splitlines())


def parse(pattern: str, text: str) -> list[dict[str, str | None]]:
    compiled = re.compile(pattern, re.MULTILINE)
    if not compiled.groupindex:
        raise ValueError("pattern must contain at least one named capture group")
    return [match.groupdict() for match in compiled.finditer(normalize_cli(text))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", required=True, help="Python regex with named groups")
    parser.add_argument("--input", required=True, type=Path, help="raw CLI fixture")
    parser.add_argument("--expected", required=True, type=Path, help="JSON array of records")
    args = parser.parse_args()
    try:
        actual: Any = parse(args.pattern, args.input.read_text(encoding="utf-8"))
        expected: Any = json.loads(args.expected.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError, re.error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if actual != expected:
        print("FAIL: parser output differs from expected JSON", file=sys.stderr)
        print(json.dumps({"actual": actual, "expected": expected}, indent=2), file=sys.stderr)
        return 1
    print(f"PASS: {len(actual)} records matched expected output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
