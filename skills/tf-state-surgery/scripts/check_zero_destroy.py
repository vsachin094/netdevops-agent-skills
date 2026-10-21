#!/usr/bin/env python3
"""Fail unless a Terraform plan JSON contains zero destroy actions."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("plan", type=Path)
args = parser.parse_args()
try:
    data = json.loads(args.plan.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    raise SystemExit(2)
changes = data.get("resource_changes", [])
destroy = []
for change in changes:
    actions = change.get("change", {}).get("actions", [])
    if "delete" in actions:
        destroy.append(change.get("address", "<unknown>"))
if destroy:
    print("ERROR: destroy actions detected:", *destroy, sep="\n", file=sys.stderr)
    raise SystemExit(1)
print(f"PASS: inspected {len(changes)} resource changes; zero destroys")
