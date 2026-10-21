#!/usr/bin/env python3
"""Validate pyats-genie parser and test structure."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_parser_structure(parser_path: Path) -> list[str]:
    errors = []
    if not parser_path.exists():
        errors.append(f"Parser file not found: {parser_path}")
        return errors
    
    content = parser_path.read_text()
    
    # Check for MetaParser class
    if "MetaParser" not in content:
        errors.append("Not a Genie MetaParser class")
    
    # Check for schema definition
    if "schema" not in content:
        errors.append("Missing schema definition")
    
    # Check for cli() method
    if "def cli" not in content:
        errors.append("Missing cli() method")
    
    # Check for Any()/Optional() usage
    if "Any()" not in content and "Optional()" not in content:
        errors.append("No Any()/Optional() in schema")
    
    # Check for validate() call
    if "self.validate" not in content:
        errors.append("Missing schema validation call")
    
    return errors

def check_fixtures(fixture_path: Path) -> list[str]:
    errors = []
    if not fixture_path.exists():
        errors.append(f"Fixture directory not found: {fixture_path}")
        return errors
    
    required_fixtures = ["healthy", "degraded", "empty", "variant"]
    for fixture in required_fixtures:
        if not list(fixture_path.glob(f"*{fixture}*")):
            errors.append(f"Missing fixture variant: {fixture}")
    
    return errors

def check_aetest_structure(test_path: Path) -> list[str]:
    errors = []
    if not test_path.exists():
        errors.append(f"AEtest file not found: {test_path}")
        return errors
    
    content = test_path.read_text()
    
    required_stages = ["setup", "test", "cleanup"]
    for stage in required_stages:
        if stage not in content:
            errors.append(f"Missing AEtest stage: {stage}")
    
    # Check for pre/post differential
    if "pre" not in content.lower() or "post" not in content.lower():
        errors.append("No pre/post differential test")
    
    return errors

def check_testbed(testbed_path: Path) -> list[str]:
    errors = []
    if not testbed_path.exists():
        errors.append(f"Testbed file not found: {testbed_path}")
        return errors
    
    content = testbed_path.read_text()
    
    if "credentials" in content and "encrypted" not in content.lower():
        errors.append("Testbed credentials not encrypted")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--parser-path", required=True)
    parser.add_argument("--fixture-path", required=True)
    parser.add_argument("--test-path", required=True)
    parser.add_argument("--testbed-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_parser_structure(Path(args.parser_path)))
    all_errors.extend(check_fixtures(Path(args.fixture_path)))
    all_errors.extend(check_aetest_structure(Path(args.test_path)))
    all_errors.extend(check_testbed(Path(args.testbed_path)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: pyats-genie validated")