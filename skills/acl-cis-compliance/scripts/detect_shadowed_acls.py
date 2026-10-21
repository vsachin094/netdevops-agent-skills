#!/usr/bin/env python3
"""Detect simple exact duplicate/subset placeholder ACL findings in JSON."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("rules", type=Path, help="JSON array with id, action, source, destination, service")
args = parser.parse_args()
try:
    rules = json.loads(args.rules.read_text(encoding="utf-8"))
    seen = {}
    findings = []
    for rule in rules:
        key = tuple(rule.get(field) for field in ("action", "source", "destination", "service"))
        if key in seen:
            findings.append({"rule": rule.get("id"), "shadowed_by": seen[key]})
        else:
            seen[key] = rule.get("id")
except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    raise SystemExit(2)
print(json.dumps({"findings": findings}, indent=2))
