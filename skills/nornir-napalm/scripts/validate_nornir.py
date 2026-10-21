#!/usr/bin/env python3
"""Validate nornir-napalm inventory and transaction handling."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_inventory(inventory_path: Path) -> list[str]:
    errors = []
    if not inventory_path.exists():
        errors.append(f"Inventory not found: {inventory_path}")
        return errors
    
    import yaml
    try:
        inv = yaml.safe_load(inventory_path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors
    
    # Check for four-layer structure
    layers = ["config.yaml", "hosts.yaml", "groups.yaml", "defaults.yaml"]
    for layer in layers:
        if not (inventory_path.parent / layer).exists():
            errors.append(f"Missing inventory layer: {layer}")
    
    # Check for secrets externalization
    if "password" in str(inv).lower() and "env" not in str(inv).lower():
        errors.append("Secrets not externalized")
    
    return errors

def check_task_structure(task_path: Path) -> list[str]:
    errors = []
    if not task_path.exists():
        errors.append(f"Task file not found: {task_path}")
        return errors
    
    content = task_path.read_text()
    
    # Check for compare_config before commit
    if "commit_config" in content and "compare_config" not in content:
        errors.append("commit_config without compare_config")
    
    # Check for discard_config on failure
    if "discard_config" not in content:
        errors.append("Missing discard_config cleanup")
    
    # Check for dry_run support
    if "dry_run" not in content:
        errors.append("No dry_run support")
    
    # Check for per-host result preservation
    if "nr.run" in content and "failed" not in content:
        errors.append("No failure handling in results")
    
    return errors

def check_driver_capability(task_path: Path) -> list[str]:
    errors = []
    content = task_path.read_text()
    
    if "napalm_get" in content:
        if "capability" not in content.lower():
            errors.append("NAPALM getter without capability check")
    
    if "napalm_configure" in content:
        if "replace" in content and "merge" not in content:
            errors.append("replace without merge fallback")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-path", required=True)
    parser.add_argument("--task-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_inventory(Path(args.inventory_path)))
    all_errors.extend(check_task_structure(Path(args.task_path)))
    all_errors.extend(check_driver_capability(Path(args.task_path)))
    
    # Run tests
    test_path = Path(args.inventory_path).parent / "tests"
    if test_path.exists():
        rc, out, err = run_cmd("pytest tests/ -v", cwd=test_path.parent)
        if rc != 0:
            all_errors.append(f"Tests failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: nornir-napalm validated")