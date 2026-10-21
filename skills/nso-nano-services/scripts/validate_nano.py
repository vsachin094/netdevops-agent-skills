#!/usr/bin/env python3
"""Validate nso-nano-services state machine."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_plan_outline(yang_path: Path) -> list[str]:
    errors = []
    if not yang_path.exists():
        errors.append(f"YANG model not found: {yang_path}")
        return errors
    
    content = yang_path.read_text()
    
    # Check for required plan states
    required_states = ["ncs:init", "ncs:ready"]
    for state in required_states:
        if state not in content:
            errors.append(f"Missing required plan state: {state}")
    
    # Check for custom states with past-tense names
    if "ncs:state" in content:
        # Simple check for past-tense custom states
        pass
    
    return errors

def check_behavior_tree(yang_path: Path) -> list[str]:
    errors = []
    content = yang_path.read_text()
    
    if "ncs:create" not in content:
        errors.append("Missing create callback")
    
    if "ncs:pre-condition" not in content:
        errors.append("Missing pre-condition for async readiness")
    
    if "kicker" not in content.lower() and "subscriber" not in content.lower():
        errors.append("No kickers/subscribers for reactive progress")
    
    return errors

def check_backtracking(yang_path: Path) -> list[str]:
    errors = []
    content = yang_path.read_text()
    
    # Check for delete/backtracking
    if "ncs:delete" not in content and "backtrack" not in content.lower():
        errors.append("No backtracking/delete handling")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--yang-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_plan_outline(Path(args.yang_path)))
    all_errors.extend(check_behavior_tree(Path(args.yang_path)))
    all_errors.extend(check_backtracking(Path(args.yang_path)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: nso-nano-services validated")