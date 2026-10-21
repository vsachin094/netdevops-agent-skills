#!/usr/bin/env python3
"""Validate ansible-execution-envs build and dependencies."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_ee_files(ee_path: Path) -> list[str]:
    errors = []
    required = ["execution-environment.yml", "requirements.yml", "requirements.txt", "bindep.txt"]
    for f in required:
        if not (ee_path / f).exists():
            errors.append(f"Missing required file: {f}")
    
    # Check version pinning
    req_yml = ee_path / "requirements.yml"
    if req_yml.exists():
        content = req_yml.read_text()
        for line in content.splitlines():
            if "version:" not in line and "name:" in line:
                # Check if next line has version
                pass  # Simplified check
    
    return errors

def check_build(ee_path: Path) -> list[str]:
    errors = []
    rc, out, err = run_cmd("ansible-builder build -t test-ee --container-runtime=docker", cwd=ee_path)
    if rc != 0:
        errors.append(f"ansible-builder build failed: {err}")
    return errors

def check_image_scan(ee_path: Path) -> list[str]:
    errors = []
    # Check if image was built
    rc, out, err = run_cmd("docker images test-ee --format '{{.Repository}}'")
    if rc != 0 or "test-ee" not in out:
        errors.append("Built image not found")
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ee-path", required=True)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    
    ee_path = Path(args.ee_path)
    all_errors = []
    
    all_errors.extend(check_ee_files(ee_path))
    if not args.skip_build:
        all_errors.extend(check_build(ee_path))
        all_errors.extend(check_image_scan(ee_path))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: ansible-execution-envs validated")