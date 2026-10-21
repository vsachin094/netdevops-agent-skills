#!/usr/bin/env python3
"""Validate pyang-xpath output correctness."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_pyang_output(yang_path: Path) -> list[str]:
    errors = []
    
    # Run pyang tree
    rc, out, err = run_cmd(f"pyang -p {yang_path.parent} -f tree {yang_path}")
    if rc != 0:
        errors.append(f"pyang tree failed: {err}")
    
    # Run pyang lint
    rc, out, err = run_cmd(f"pyang -p {yang_path.parent} --lint {yang_path}")
    if rc != 0:
        errors.append(f"pyang lint failed: {err}")
    
    return errors

def check_xpath_generation(yang_path: Path) -> list[str]:
    errors = []
    
    # Generate sample XML skeleton
    rc, out, err = run_cmd(f"pyang -p {yang_path.parent} -f sample-xml-skeleton {yang_path}")
    if rc != 0:
        errors.append(f"sample-xml-skeleton failed: {err}")
    
    # Check for namespace preservation
    if "xmlns" not in out:
        errors.append("Generated XML missing namespace declarations")
    
    return errors

def check_restconf_paths(yang_path: Path) -> list[str]:
    errors = []
    
    rc, out, err = run_cmd(f"pyang -p {yang_path.parent} -f restconf {yang_path}")
    if rc != 0:
        errors.append(f"RESTCONF path generation failed: {err}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--yang-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_pyang_output(Path(args.yang_path)))
    all_errors.extend(check_xpath_generation(Path(args.yang_path)))
    all_errors.extend(check_restconf_paths(Path(args.yang_path)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: pyang-xpath validated")