#!/usr/bin/env python3
"""Validate tf-aws-networking module structure."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_module_structure(tf_path: Path) -> list[str]:
    errors = []
    required = ["main.tf", "variables.tf", "outputs.tf", "versions.tf"]
    for f in required:
        if not (tf_path / f).exists():
            errors.append(f"Missing required file: {f}")
    
    return errors

def check_aws_validation(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for CIDR validation
        if "cidr" in content.lower() and "validation" not in content.lower():
            errors.append(f"{tf_file.name}: CIDR without validation block")
        
        # Check for flow logs
        if "aws_vpc" in content and "flow_log" not in content:
            errors.append(f"VPC without flow logs")
        
        # Check for TGW route table associations
        if "aws_ec2_transit_gateway_vpc_attachment" in content:
            if "aws_ec2_transit_gateway_route_table_association" not in content:
                errors.append(f"TGW attachment without route table association")
    
    return errors

def check_naming_convention(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        if "resource" in content:
            # Check for consistent naming
            if "name =" in content and "var." not in content:
                errors.append(f"Hardcoded name in {tf_file.name}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tf-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_module_structure(Path(args.tf_path)))
    all_errors.extend(check_aws_validation(Path(args.tf_path)))
    all_errors.extend(check_naming_convention(Path(args.tf_path)))
    
    rc, out, err = run_cmd("terraform fmt -check && terraform init -backend=false && terraform validate", cwd=args.tf_path)
    if rc != 0:
        all_errors.append(f"Terraform validation failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: tf-aws-networking validated")