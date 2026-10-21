#!/usr/bin/env python3
"""Validate netops-cli-packaging CLI behavior."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_cli_structure(cli_path: Path) -> list[str]:
    errors = []
    content = cli_path.read_text()
    
    # Check for required options
    required_options = ["--inventory", "--limit", "--dry-run", "--apply", "--output", "--verbose", "--timeout"]
    for opt in required_options:
        if opt not in content:
            errors.append(f"Missing required option: {opt}")
    
    # Check for exit codes
    exit_codes = ["0", "1", "2", "3", "130"]
    for code in exit_codes:
        if f"Exit code {code}" not in content and f"typer.Exit({code})" not in content:
            errors.append(f"Missing exit code documentation: {code}")
    
    # Check for credential handling
    if "getpass" not in content and "prompt" not in content.lower():
        errors.append("No interactive credential prompt")
    
    # Check for JSON output
    if "json" not in content.lower():
        errors.append("No JSON output mode")
    
    return errors

def check_packaging(pkg_path: Path) -> list[str]:
    errors = []
    
    # Check pyproject.toml
    pyproject = pkg_path / "pyproject.toml"
    if not pyproject.exists():
        errors.append("Missing pyproject.toml")
    else:
        content = pyproject.read_text()
        if "[project.scripts]" not in content:
            errors.append("Missing [project.scripts] entry point")
        if "dependencies" not in content:
            errors.append("Missing dependencies in pyproject.toml")
    
    # Check for test layout
    if not (pkg_path / "tests").exists():
        errors.append("Missing tests/ directory")
    
    return errors

def run_cli_tests(cli_path: Path) -> list[str]:
    errors = []
    
    # Test help
    rc, out, err = run_cmd("python -m netops_cli --help", cwd=cli_path.parent)
    if rc != 0:
        errors.append(f"Help command failed: {err}")
    
    # Test invalid combination
    rc, out, err = run_cmd("python -m netops_cli --check --apply", cwd=cli_path.parent)
    if rc == 0:
        errors.append("Should fail on mutually exclusive --check/--apply")
    
    # Test dry-run default
    rc, out, err = run_cmd("python -m netops_cli --inventory inv.yml", cwd=cli_path.parent)
    if "dry-run" not in out.lower() and "check mode" not in out.lower():
        errors.append("Default should be dry-run/check mode")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli-path", required=True)
    args = parser.parse_args()
    
    cli_path = Path(args.cli_path)
    all_errors = []
    
    all_errors.extend(check_cli_structure(cli_path))
    all_errors.extend(check_packaging(cli_path))
    all_errors.extend(run_cli_tests(cli_path))
    
    # Run pytest
    test_path = cli_path.parent / "tests"
    if test_path.exists():
        rc, out, err = run_cmd("pytest tests/ -v", cwd=cli_path.parent)
        if rc != 0:
            all_errors.append(f"Tests failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: netops-cli-packaging validated")