#!/usr/bin/env python3
"""Validate ansible-dynamic-inventory plugin configuration."""

import subprocess
import sys
import yaml
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_inventory_config(config_path: Path) -> list[str]:
    errors = []
    if not config_path.exists():
        errors.append(f"Inventory config not found: {config_path}")
        return errors
    
    try:
        config = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors
    
    required_keys = ["plugin", "api_endpoint", "token", "keyed_groups"]
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")
    
    # Check keyed_groups structure
    if "keyed_groups" in config:
        for group in config["keyed_groups"]:
            if "key" not in group:
                errors.append("keyed_groups entries must have 'key'")
            if "prefix" not in group:
                errors.append("keyed_groups entries should have 'prefix'")
    
    # Check compose has ansible_host
    if "compose" in config:
        if "ansible_host" not in config["compose"]:
            errors.append("compose should define ansible_host")
    
    return errors

def run_inventory_test(config_path: Path) -> list[str]:
    errors = []
    rc, out, err = run_cmd(f"ansible-inventory -i {config_path} --list", cwd=config_path.parent)
    if rc != 0:
        errors.append(f"ansible-inventory failed: {err}")
    else:
        # Verify output is valid JSON
        try:
            import json
            json.loads(out)
        except json.JSONDecodeError:
            errors.append("ansible-inventory output is not valid JSON")
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to inventory plugin config")
    args = parser.parse_args()
    
    config_path = Path(args.config)
    all_errors = []
    
    all_errors.extend(check_inventory_config(config_path))
    all_errors.extend(run_inventory_test(config_path))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ansible-dynamic-inventory validated")