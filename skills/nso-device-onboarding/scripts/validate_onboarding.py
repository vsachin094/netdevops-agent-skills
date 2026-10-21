#!/usr/bin/env python3
"""Validate nso-device-onboarding sequence."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_onboarding_sequence(nso_path: Path) -> list[str]:
    errors = []
    content = nso_path.read_text()
    
    # Check for required steps
    required_steps = [
        "authgroup",
        "device-type",
        "ned-id",
        "device-group",
        "fetch-ssh-host-keys",
        "sync-from",
        "check-sync",
        "compare-config",
    ]
    
    for step in required_steps:
        if step not in content:
            errors.append(f"Missing onboarding step: {step}")
    
    # Check for dry-run before commit
    if "commit dry-run" not in content:
        errors.append("Missing dry-run before commit")
    
    # Check for credential externalization
    if "password" in content.lower() and "secret" not in content.lower():
        errors.append("Credentials not externalized")
    
    return errors

def check_ned_validation(nso_path: Path) -> list[str]:
    errors = []
    content = nso_path.read_text()
    
    if "ned package" not in content.lower() and "ned version" not in content.lower():
        errors.append("No NED version validation")
    
    return errors

def check_idempotency(nso_path: Path) -> list[str]:
    errors = []
    content = nso_path.read_text()
    
    if "reconcil" not in content.lower():
        errors.append("No reconciliation for idempotent re-run")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--nso-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_onboarding_sequence(Path(args.nso_path)))
    all_errors.extend(check_ned_validation(Path(args.nso_path)))
    all_errors.extend(check_idempotency(Path(args.nso_path)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: nso-device-onboarding validated")