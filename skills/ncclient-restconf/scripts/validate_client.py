#!/usr/bin/env python3
"""Validate ncclient-restconf client transaction handling."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_client_structure(client_path: Path) -> list[str]:
    errors = []
    content = client_path.read_text()
    
    # Check for capability check
    if "server_capabilities" not in content:
        errors.append("Missing capability check")
    
    # Check for lock/unlock
    if "lock(" not in content:
        errors.append("Missing datastore lock")
    if "unlock(" not in content:
        errors.append("Missing datastore unlock")
    
    # Check for commit/discard
    if "commit(" not in content:
        errors.append("Missing commit")
    if "discard_changes()" not in content:
        errors.append("Missing discard_changes on error")
    
    # Check for confirmed commit
    if "confirmed" not in content:
        errors.append("Missing confirmed commit for risky changes")
    
    # Check for hostkey verification
    if "hostkey_verify=True" not in content and "hostkey_verify=False" in content:
        errors.append("hostkey_verify disabled (security issue)")
    
    # Check for try/except/finally
    if "try:" not in content:
        errors.append("Missing try/except for transaction handling")
    if "finally:" not in content:
        errors.append("Missing finally block for cleanup")
    
    return errors

def check_restconf_client(client_path: Path) -> list[str]:
    errors = []
    content = client_path.read_text()
    
    if "httpx.Client" not in content:
        errors.append("RESTCONF client should use httpx.Client")
    
    if "timeout" not in content:
        errors.append("Missing timeout configuration")
    
    if "verify=True" not in content and "verify=False" in content:
        errors.append("TLS verification disabled")
    
    # Check for retry only on safe methods
    if "retry" in content:
        if "POST" in content or "PATCH" in content:
            if "idempotency" not in content.lower():
                errors.append("Retry on non-idempotent methods without idempotency key")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-path", required=True)
    args = parser.parse_args()
    
    client_path = Path(args.client_path)
    all_errors = []
    
    all_errors.extend(check_client_structure(client_path))
    all_errors.extend(check_restconf_client(client_path))
    
    # Run tests if exist
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
        print("OK: ncclient-restconf validated")