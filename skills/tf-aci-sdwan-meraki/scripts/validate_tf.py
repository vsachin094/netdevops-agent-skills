#!/usr/bin/env python3
"""Validate tf-aci-sdwan-meraki hierarchy and async handling."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_hierarchy(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for for_each with stable keys
        if "for_each" in content:
            if "count.index" in content:
                errors.append(f"{tf_file.name}: for_each using count.index (unstable)")
        
        # Check for depends_on
        if "resource" in content and "depends_on" not in content:
            # Check if resource references other resources
            if "." in content and "resource" in content:
                pass  # Could add more sophisticated check
    
    return errors

def check_async_handling(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for timeouts
        if "resource" in content and "timeouts" not in content:
            errors.append(f"{tf_file.name}: missing timeouts block")
        
        # Check for provisioner local-exec with sleep
        if "local-exec" in content and "sleep" in content:
            errors.append(f"{tf_file.name}: using sleep for async (anti-pattern)")
    
    return errors

def check_provider_versions(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        if "required_providers" in content:
            if "version" not in content:
                errors.append(f"{tf_file.name}: provider without version constraint")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tf-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_hierarchy(Path(args.tf_path)))
    all_errors.extend(check_async_handling(Path(args.tf_path)))
    all_errors.extend(check_provider_versions(Path(args.tf_path)))
    
    # Run terraform validation
    rc, out, err = run_cmd("terraform fmt -check && terraform init -backend=false && terraform validate", cwd=args.tf_path)
    if rc != 0:
        all_errors.append(f"Terraform validation failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: tf-aci-sdwan-meraki validated")