#!/usr/bin/env python3
"""Run a TextFSM template against raw input and expected JSON records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    args = parser.parse_args()
    try:
        import textfsm
        with args.template.open(encoding="utf-8") as template_file:
            table = textfsm.TextFSM(template_file)
        actual = table.ParseText(args.input.read_text(encoding="utf-8"))
        actual = [dict(zip(table.header, row)) for row in actual]
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
    except (ImportError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if actual != expected:
        print(json.dumps({"actual": actual, "expected": expected}, indent=2), file=sys.stderr)
        return 1
    print(f"PASS: {len(actual)} TextFSM records matched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
