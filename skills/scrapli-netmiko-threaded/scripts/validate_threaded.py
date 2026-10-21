#!/usr/bin/env python3
"""Validate scrapli-netmiko-threaded concurrency and results."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_runner_structure(runner_path: Path) -> list[str]:
    errors = []
    if not runner_path.exists():
        errors.append(f"Runner file not found: {runner_path}")
        return errors
    
    content = runner_path.read_text()
    
    # Check for ThreadPoolExecutor with max_workers
    if "ThreadPoolExecutor" not in content:
        errors.append("Missing ThreadPoolExecutor")
    
    if "max_workers" not in content:
        errors.append("Missing max_workers limit")
    
    # Check for exception handling in worker
    if "try:" not in content:
        errors.append("No try/except in worker")
    
    # Check for connection per worker
    if "with" not in content and "connect" in content:
        errors.append("No context manager for connection")
    
    # Check for result schema
    required_fields = ["device", "status", "duration", "error"]
    for field in required_fields:
        if field not in content:
            errors.append(f"Result schema missing: {field}")
    
    # Check for as_completed or wait
    if "as_completed" not in content and "wait" not in content:
        errors.append("No result collection mechanism")
    
    return errors

def check_inventory_validation(inventory_path: Path) -> list[str]:
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
    
    # Check for required fields
    for device in inv.get("devices", []):
        required = ["name", "host", "platform", "username"]
        for field in required:
            if field not in device:
                errors.append(f"Device {device.get('name', 'unknown')} missing: {field}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner-path", required=True)
    parser.add_argument("--inventory-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_runner_structure(Path(args.runner_path)))
    all_errors.extend(check_inventory_validation(Path(args.inventory_path)))
    
    # Run tests
    test_path = Path(args.runner_path).parent / "tests"
    if test_path.exists():
        rc, out, err = run_cmd("pytest tests/ -v", cwd=test_path.parent)
        if rc != 0:
            all_errors.append(f"Tests failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: scrapli-netmiko-threaded validated")