#!/usr/bin/env python3
"""Validate netbox-nautobot-api idempotency and error handling."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_client_structure(client_path: Path) -> list[str]:
    errors = []
    content = client_path.read_text()
    
    # Check for natural key lookups before create
    if "create(" in content and "get(" not in content:
        errors.append("Create without prior lookup (not idempotent)")
    
    # Check for GraphQL bulk reads
    if "graphql" not in content.lower() and "query" not in content.lower():
        errors.append("No GraphQL bulk read for nested objects")
    
    # Check for pagination handling
    if "paginate" not in content.lower() and "page" not in content.lower():
        errors.append("No pagination handling for list endpoints")
    
    # Check for rate limit handling
    if "429" not in content and "rate" not in content.lower():
        errors.append("No rate limit handling (429)")
    
    # Check for token externalization
    if "NETBOX_TOKEN" not in content and "NAUTOBOT_TOKEN" not in content:
        errors.append("Token not externalized")
    
    return errors

def check_dry_run_support(client_path: Path) -> list[str]:
    errors = []
    content = client_path.read_text()
    
    if "dry" not in content.lower() and "diff" not in content.lower():
        errors.append("No dry-run or diff support")
    
    return errors

def check_error_handling(client_path: Path) -> list[str]:
    errors = []
    content = client_path.read_text()
    
    for code in ["401", "403", "404", "409", "429", "500"]:
        if code not in content:
            errors.append(f"Missing error handling for {code}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-path", required=True)
    args = parser.parse_args()
    
    client_path = Path(args.client_path)
    all_errors = []
    
    all_errors.extend(check_client_structure(client_path))
    all_errors.extend(check_dry_run_support(client_path))
    all_errors.extend(check_error_handling(client_path))
    
    # Run tests
    test_path = client_path.parent / "tests"
    if test_path.exists():
        rc, out, err = run_cmd("pytest tests/ -v", cwd=client_path.parent)
        if rc != 0:
            all_errors.append(f"Tests failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: netbox-nautobot-api validated")