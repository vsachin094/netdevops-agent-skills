#!/usr/bin/env python3
"""Validate tf-azure-gcp-networking module structure."""

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

def check_azure_validation(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for hub/spoke peering
        if "azurerm_virtual_network_peering" in content:
            if "allow_gateway_transit" not in content:
                errors.append(f"VNet peering missing allow_gateway_transit")
            if "use_remote_gateways" not in content:
                errors.append(f"VNet peering missing use_remote_gateways")
        
        # Check for flow logs
        if "azurerm_network_watcher_flow_log" not in content and "azurerm_virtual_network" in content:
            errors.append(f"VNet without flow logs")
    
    return errors

def check_gcp_validation(tf_path: Path) -> list[str]:
    errors = []
    for tf_file in tf_path.glob("*.tf"):
        content = tf_file.read_text()
        
        # Check for Shared VPC
        if "google_compute_shared_vpc" in content:
            if "host_project" not in content:
                errors.append(f"Shared VPC missing host_project")
        
        # Check for Cloud NAT
        if "google_compute_router_nat" in content:
            if "nat_ip_allocate_option" not in content:
                errors.append(f"Cloud NAT missing nat_ip_allocate_option")
        
        # Check for custom routes
        if "google_compute_route" in content:
            if "next_hop" not in content:
                errors.append(f"Route missing next_hop")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tf-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_module_structure(Path(args.tf_path)))
    all_errors.extend(check_azure_validation(Path(args.tf_path)))
    all_errors.extend(check_gcp_validation(Path(args.tf_path)))
    
    rc, out, err = run_cmd("terraform fmt -check && terraform init -backend=false && terraform validate", cwd=args.tf_path)
    if rc != 0:
        all_errors.append(f"Terraform validation failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: tf-azure-gcp-networking validated")