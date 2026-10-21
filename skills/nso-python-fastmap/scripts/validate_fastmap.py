#!/usr/bin/env python3
"""Validate nso-python-fastmap transaction boundaries."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_callback_structure(callback_path: Path) -> list[str]:
    errors = []
    if not callback_path.exists():
        errors.append(f"Callback file not found: {callback_path}")
        return errors
    
    content = callback_path.read_text()
    
    # Check for cb_create
    if "cb_create" not in content:
        errors.append("Missing cb_create callback")
    
    # Check for transaction purity
    if "ncs.maapi.single_write_trans" in content:
        errors.append("Uses separate MAAPI transaction (breaks FASTMAP)")
    
    if "ncs.maapi.Maapi" in content and "tctx" not in content:
        errors.append("MAAPI usage without transaction context")
    
    # Check for template apply with service
    if "ncs.template.Template(service)" not in content:
        errors.append("Template.apply not using service transaction")
    
    # Check for validation before apply
    if "leafref" in content.lower() and "validate" not in content.lower():
        errors.append("Leafref validation before Template.apply")
    
    return errors

def check_resource_allocation(callback_path: Path) -> list[str]:
    errors = []
    content = callback_path.read_text()
    
    if "allocate" in content.lower():
        if "deterministic" not in content.lower():
            errors.append("Resource allocation not deterministic")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--callback-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_callback_structure(Path(args.callback_path)))
    all_errors.extend(check_resource_allocation(Path(args.callback_path)))
    
    # Run NSO package compile
    package_root = Path(args.callback_path).parent.parent
    if (package_root / "package-meta-data.xml").exists():
        rc, out, err = run_cmd("ncs-make-package --compile", cwd=package_root)
        if rc != 0:
            all_errors.append(f"Package compile failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: nso-python-fastmap validated")