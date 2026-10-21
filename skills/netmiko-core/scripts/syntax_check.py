#!/usr/bin/env python3
"""Compile-check a Netmiko script without importing device libraries."""
from __future__ import annotations
import argparse
import py_compile
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("file", type=Path)
args = parser.parse_args()
try:
    py_compile.compile(str(args.file), doraise=True)
except py_compile.PyCompileError as exc:
    print(exc, file=sys.stderr)
    raise SystemExit(1)
print(f"PASS: syntax valid: {args.file}")
