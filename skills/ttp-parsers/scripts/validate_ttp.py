#!/usr/bin/env python3
"""Validate ttp-parsers template and fixture structure."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_template_structure(template_path: Path) -> list[str]:
    errors = []
    if not template_path.exists():
        errors.append(f"Template file not found: {template_path}")
        return errors
    
    content = template_path.read_text()
    
    # Check for group definitions
    if "<group" not in content:
        errors.append("Missing <group> definitions")
    
    # Check for _start_ matchers
    if "_start_" not in content:
        errors.append("Missing _start_ matchers for record boundaries")
    
    # Check for matchers (IP, MAC, etc.)
    matchers = ["IP", "MAC", "PREFIX", "WORD", "DIGIT"]
    has_matcher = any(m in content for m in matchers)
    if not has_matcher:
        errors.append("No type matchers (IP, MAC, PREFIX, etc.) found")
    
    # Check for ignore rules
    if "ignore" not in content.lower():
        errors.append("No ignore rules for banners/prompts")
    
    return errors

def check_fixtures(fixture_path: Path) -> list[str]:
    errors = []
    if not fixture_path.exists():
        errors.append(f"Fixture directory not found: {fixture_path}")
        return errors
    
    required = ["complete", "empty", "multi_section", "reordered", "malformed"]
    for variant in required:
        if not list(fixture_path.glob(f"*{variant}*")):
            errors.append(f"Missing fixture variant: {variant}")
    
    return errors

def check_output_schema(schema_path: Path) -> list[str]:
    errors = []
    if not schema_path.exists():
        errors.append(f"Expected output schema not found: {schema_path}")
        return errors
    
    import json
    try:
        json.loads(schema_path.read_text())
    except json.JSONDecodeError:
        errors.append("Expected output schema is not valid JSON")
    
    return errors

def run_ttp_test(template_path: Path, fixture_path: Path) -> list[str]:
    errors = []
    # Run TTP on fixtures
    for fixture in fixture_path.glob("*.txt"):
        rc, out, err = run_cmd(f"ttp -d {template_path} {fixture}", cwd=template_path.parent)
        if rc != 0:
            errors.append(f"TTP failed on {fixture.name}: {err}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-path", required=True)
    parser.add_argument("--fixture-path", required=True)
    parser.add_argument("--schema-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_template_structure(Path(args.template_path)))
    all_errors.extend(check_fixtures(Path(args.fixture_path)))
    all_errors.extend(check_output_schema(Path(args.schema_path)))
    all_errors.extend(run_ttp_test(Path(args.template_path), Path(args.fixture_path)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ttp-parsers validated")