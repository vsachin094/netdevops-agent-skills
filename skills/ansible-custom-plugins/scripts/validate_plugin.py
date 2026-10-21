#!/usr/bin/env python3
"""Validate ansible-custom-plugins structure and tests."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_plugin_structure(plugin_path: Path) -> list[str]:
    errors = []
    # Check for module, filter, or connection plugin structure
    has_module = (plugin_path / "plugins" / "modules").exists()
    has_filter = (plugin_path / "plugins" / "filter").exists()
    has_connection = (plugin_path / "plugins" / "connection").exists()
    has_httapi = (plugin_path / "plugins" / "httpapi").exists()
    
    if not any([has_module, has_filter, has_connection, has_httapi]):
        errors.append("No plugin directories found (modules/filter/connection/httpapi)")
    
    # Check for documentation
    for plugin_dir in ["modules", "filter", "connection", "httpapi"]:
        dir_path = plugin_path / "plugins" / plugin_dir
        if dir_path.exists():
            for plugin_file in dir_path.glob("*.py"):
                content = plugin_file.read_text()
                if "DOCUMENTATION" not in content:
                    errors.append(f"Missing DOCUMENTATION in {plugin_file}")
                if "EXAMPLES" not in content:
                    errors.append(f"Missing EXAMPLES in {plugin_file}")
                if "RETURN" not in content and plugin_dir == "modules":
                    errors.append(f"Missing RETURN in {plugin_file}")
    return errors

def check_ansible_test(plugin_path: Path) -> list[str]:
    rc, out, err = run_cmd("ansible-test sanity --skip-test import", cwd=plugin_path)
    if rc != 0:
        return [f"ansible-test sanity failed: {err}"]
    return []

def check_unit_tests(plugin_path: Path) -> list[str]:
    test_dir = plugin_path / "tests"
    if not test_dir.exists():
        return ["Missing tests/ directory"]
    rc, out, err = run_cmd("pytest tests/ -v", cwd=plugin_path)
    if rc != 0:
        return [f"Unit tests failed: {err}"]
    return []

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-path", required=True)
    args = parser.parse_args()
    
    plugin_path = Path(args.plugin_path)
    all_errors = []
    
    all_errors.extend(check_plugin_structure(plugin_path))
    all_errors.extend(check_ansible_test(plugin_path))
    all_errors.extend(check_unit_tests(plugin_path))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ansible-custom-plugins validated")