#!/usr/bin/env python3
"""Validate ansible-netcli-playbooks syntax and idempotency."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_playbook_syntax(playbook_path: Path) -> list[str]:
    errors = []
    for playbook in playbook_path.glob("*.yml"):
        rc, out, err = run_cmd(f"ansible-playbook --syntax-check {playbook}")
        if rc != 0:
            errors.append(f"Syntax check failed for {playbook.name}: {err}")
    return errors

def check_ansible_lint(playbook_path: Path) -> list[str]:
    rc, out, err = run_cmd("ansible-lint", cwd=playbook_path)
    if rc != 0:
        return [f"ansible-lint failed: {out}"]
    return []

def check_check_mode(playbook_path: Path) -> list[str]:
    errors = []
    for playbook in playbook_path.glob("*.yml"):
        rc, out, err = run_cmd(f"ansible-playbook {playbook} --check", cwd=playbook_path)
        if rc != 0:
            errors.append(f"Check mode failed for {playbook.name}: {err}")
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--playbook-path", required=True)
    args = parser.parse_args()
    
    playbook_path = Path(args.playbook_path)
    all_errors = []
    
    all_errors.extend(check_playbook_syntax(playbook_path))
    all_errors.extend(check_ansible_lint(playbook_path))
    all_errors.extend(check_check_mode(playbook_path))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ansible-netcli-playbooks validated")