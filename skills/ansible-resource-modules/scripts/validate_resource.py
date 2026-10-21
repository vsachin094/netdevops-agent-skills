#!/usr/bin/env python3
"""Validate ansible-resource-modules usage."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_resource_module_usage(playbook_path: Path) -> list[str]:
    errors = []
    content = playbook_path.read_text()
    
    # Check for legacy config modules
    legacy_modules = ["ios_config", "nxos_config", "eos_config", "cli_config"]
    for mod in legacy_modules:
        if mod in content:
            errors.append(f"Uses legacy module: {mod} (prefer resource modules)")
    
    # Check for state parameter
    if "state:" not in content:
        errors.append("No state parameter found in resource module tasks")
    
    # Check for check mode support
    if "--check" not in content and "check_mode" not in content:
        errors.append("No check-mode usage found")
    
    return errors

def check_idempotency(playbook_path: Path) -> list[str]:
    errors = []
    # Run in check mode twice
    rc, out, err = run_cmd(f"ansible-playbook {playbook_path} --check")
    if rc != 0:
        errors.append(f"First check run failed: {err}")
    
    rc, out, err = run_cmd(f"ansible-playbook {playbook_path} --check")
    if rc != 0:
        errors.append(f"Second check run failed: {err}")
    if "changed=true" in out or "changed=True" in out:
        errors.append("Second check run shows changes (not idempotent)")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--playbook-path", required=True)
    args = parser.parse_args()
    
    playbook_path = Path(args.playbook_path)
    all_errors = []
    
    all_errors.extend(check_resource_module_usage(playbook_path))
    all_errors.extend(check_idempotency(playbook_path))
    
    rc, out, err = run_cmd(f"ansible-playbook --syntax-check {playbook_path}")
    if rc != 0:
        all_errors.append(f"Syntax check failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ansible-resource-modules validated")