#!/usr/bin/env python3
"""Parse JSON and XML payload files; fail on syntax errors."""
from __future__ import annotations
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+", type=Path)
args = parser.parse_args()
for path in args.files:
    try:
        if path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        else:
            ET.parse(path)
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"ERROR {path}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"OK {path}")
