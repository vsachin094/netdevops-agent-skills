#!/usr/bin/env python3
"""Validate ansible-linux-networking role structure and idempotency."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_role_structure(role_path: Path) -> list[str]:
    errors = []
    required = [
        "defaults/main.yml",
        "vars/main.yml",
        "tasks/main.yml",
        "handlers/main.yml",
        "meta/argument_specs.yml",
        "molecule/default/molecule.yml",
        "molecule/default/converge.yml",
        "molecule/default/verify.yml",
    ]
    for f in required:
        if not (role_path / f).exists():
            errors.append(f"Missing required file: {f}")
    return errors

def check_ansible_lint(role_path: Path) -> list[str]:
    rc, out, err = run_cmd("ansible-lint", cwd=role_path)
    if rc != 0:
        return [f"ansible-lint failed: {out}"]
    return []

def check_molecule_idempotence(role_path: Path) -> list[str]:
    # Run molecule converge twice and check for changes
    rc, out, err = run_cmd("molecule converge", cwd=role_path)
    if rc != 0:
        return [f"First converge failed: {err}"]
    
    rc, out, err = run_cmd("molecule converge", cwd=role_path)
    if rc != 0:
        return [f"Second converge failed: {err}"]
    
    if "changed=0" not in out and "ok=" not in out:
        return ["Second converge shows changes (not idempotent)"]
    return []

def check_syntax(role_path: Path) -> list[str]:
    rc, out, err = run_cmd("ansible-playbook --syntax-check molecule/default/converge.yml", cwd=role_path)
    if rc != 0:
        return [f"Syntax check failed: {err}"]
    return []

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--role-path", required=True, help="Path to ansible role")
    parser.add_argument("--skip-molecule", action="store_true", help="Skip molecule tests")
    args = parser.parse_args()
    
    role_path = Path(args.role_path)
    all_errors = []
    
    all_errors.extend(check_role_structure(role_path))
    all_errors.extend(check_syntax(role_path))
    all_errors.extend(check_ansible_lint(role_path))
    
    if not args.skip_molecule:
        all_errors.extend(check_molecule_idempotence(role_path))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ansible-linux-networking role validated")