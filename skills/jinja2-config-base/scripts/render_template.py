#!/usr/bin/env python3
"""Render a Jinja2 template with strict undefined-variable behavior."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

parser = argparse.ArgumentParser()
parser.add_argument("template", type=Path)
parser.add_argument("data", type=Path)
args = parser.parse_args()
payload = yaml.safe_load(args.data.read_text(encoding="utf-8"))
env = Environment(loader=FileSystemLoader(str(args.template.parent)), undefined=StrictUndefined,
                  trim_blocks=True, lstrip_blocks=True)
print(env.get_template(args.template.name).render(**(payload or {})))
