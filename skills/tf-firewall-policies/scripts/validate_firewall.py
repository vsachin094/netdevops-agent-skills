#!/usr/bin/env python3
"""Validate tf-firewall-policies rule stability."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_rule_stability(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for for_each with stable keys
        if "for_each" in content:
            if "count.index" in content:
                errors.append(f"{tf_file.name}: for_each using count.index (unstable)")
            if "keys" not in content and "values" not in content:
                pass  # Could add more sophisticated check
    
    return errors

def check_rule_completeness(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for required fields in rule objects
        required_fields = ["source", "destination", "service", "action", "log", "owner"]
        for field in required_fields:
            if field not in content:
                errors.append(f"Rule missing required field: {field}")
    
    return errors

def check_shadow_analysis(tf_path: Path) -> list[str]:
    errors = []
    # Check for shadow analysis script
    scripts = list(Path(tf_path).glob("scripts/*.py"))
    if not scripts:
        errors.append("No shadow analysis script found")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tf-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_rule_stability(Path(args.tf_path)))
    all_errors.extend(check_rule_completeness(Path(args.tf_path)))
    all_errors.extend(check_shadow_analysis(Path(args.tf_path)))
    
    rc, out, err = run_cmd("terraform fmt -check && terraform init -backend=false && terraform validate", cwd=args.tf_path)
    if rc != 0:
        all_errors.append(f"Terraform validation failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: tf-firewall-policies validated")