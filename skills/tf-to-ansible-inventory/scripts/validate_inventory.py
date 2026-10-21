#!/usr/bin/env python3
"""Validate tf-ansible-inventory output schema."""

import subprocess
import sys
import json
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_output_schema(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for output with type and sensitivity
        if "output" in content:
            if "type" not in content:
                errors.append(f"Output missing type constraint")
            if "sensitive" not in content and "password" in content.lower():
                errors.append(f"Sensitive output not marked sensitive")
    
    return errors

def check_inventory_rendering(tf_path: Path) -> list[str]:
    errors = []
    # Run terraform plan and check outputs
    rc, out, err = run_cmd("terraform init -backend=false && terraform plan -out=tfplan", cwd=tf_path)
    if rc != 0:
        errors.append(f"Terraform plan failed: {err}")
        return errors
    
    rc, out, err = run_cmd("terraform show -json tfplan", cwd=tf_path)
    if rc != 0:
        errors.append(f"Terraform show failed: {err}")
        return errors
    
    try:
        plan = json.loads(out)
        outputs = plan.get("planned_values", {}).get("outputs", {})
        
        for name, output in outputs.items():
            if "value" not in output:
                errors.append(f"Output {name} missing value")
            if "sensitive" in output and output["sensitive"] and "type" not in output:
                errors.append(f"Sensitive output {name} missing type")
    except json.JSONDecodeError:
        errors.append("Plan JSON decode failed")
    
    return errors

def check_ansible_inventory(tf_path: Path) -> list[str]:
    errors = []
    # Check that inventory rendering script exists
    scripts = list(Path(tf_path).glob("scripts/*.py")) + list(Path(tf_path).glob("scripts/*.sh"))
    if not scripts:
        errors.append("No inventory rendering script found")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tf-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_output_schema(Path(args.tf_path)))
    all_errors.extend(check_inventory_rendering(Path(args.tf_path)))
    all_errors.extend(check_ansible_inventory(Path(args.tf_path)))
    
    rc, out, err = run_cmd("terraform fmt -check && terraform init -backend=false && terraform validate", cwd=args.tf_path)
    if rc != 0:
        all_errors.append(f"Terraform validation failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: tf-ansible-inventory validated")