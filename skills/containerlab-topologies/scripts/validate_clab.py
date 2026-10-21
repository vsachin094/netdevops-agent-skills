#!/usr/bin/env python3
"""Perform dependency-free structural checks on a Containerlab YAML file."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml

parser = argparse.ArgumentParser()
parser.add_argument("topology", type=Path)
args = parser.parse_args()
try:
    doc = yaml.safe_load(args.topology.read_text(encoding="utf-8"))
    topology = doc["topology"]
    nodes = topology["nodes"]
    links = topology.get("links", [])
    assert isinstance(nodes, dict) and nodes
    for name, node in nodes.items():
        assert isinstance(name, str) and node.get("kind") and node.get("image")
    for link in links:
        endpoints = link["endpoints"]
        assert len(endpoints) == 2
        for endpoint in endpoints:
            node, interface = endpoint.split(":", 1)
            assert node in nodes and interface
except (OSError, KeyError, TypeError, ValueError, AssertionError, yaml.YAMLError) as exc:
    print(f"ERROR: invalid topology: {exc}", file=sys.stderr)
    raise SystemExit(1)
print(f"PASS: {len(nodes)} nodes, {len(links)} links")
