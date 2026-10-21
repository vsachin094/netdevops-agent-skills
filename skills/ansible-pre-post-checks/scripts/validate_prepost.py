#!/usr/bin/env python3
"""Validate ansible-pre-post-checks playbook structure."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_block_rescue_structure(playbook_path: Path) -> list[str]:
    errors = []
    content = playbook_path.read_text()
    if "block:" not in content:
        errors.append("Missing 'block:' section")
    if "rescue:" not in content:
        errors.append("Missing 'rescue:' section")
    if "always:" not in content:
        errors.append("Missing 'always:' section")
    return errors

def check_baseline_postcheck(playbook_path: Path) -> list[str]:
    errors = []
    content = playbook_path.read_text()
    # Check for baseline capture
    if "gather_network_resources" not in content and "cli_parse" not in content:
        errors.append("No baseline capture mechanism found")
    # Check for assertions
    if "assert:" not in content:
        errors.append("No post-check assertions found")
    return errors

def check_rollback(playbook_path: Path) -> list[str]:
    errors = []
    content = playbook_path.read_text()
    if "rescue:" in content:
        rescue_section = content.split("rescue:")[1].split("\n")[0:20]
        rescue_text = "\n".join(rescue_section)
        if "config" not in rescue_text and "command" not in rescue_text:
            errors.append("Rescue section should contain rollback commands")
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--playbook-path", required=True)
    args = parser.parse_args()
    
    playbook_path = Path(args.playbook_path)
    all_errors = []
    
    all_errors.extend(check_block_rescue_structure(playbook_path))
    all_errors.extend(check_baseline_postcheck(playbook_path))
    all_errors.extend(check_rollback(playbook_path))
    
    # Also run syntax and lint
    rc, out, err = run_cmd(f"ansible-playbook --syntax-check {playbook_path}")
    if rc != 0:
        all_errors.append(f"Syntax check failed: {err}")
    
    rc, out, err = run_cmd("ansible-lint", cwd=playbook_path.parent)
    if rc != 0:
        all_errors.append(f"ansible-lint failed: {out}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ansible-pre-post-checks validated")