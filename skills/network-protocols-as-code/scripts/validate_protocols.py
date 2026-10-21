#!/usr/bin/env python3
"""Validate network-protocols-as-code vendor rendering."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_intent_model(model_path: Path) -> list[str]:
    errors = []
    if not model_path.exists():
        errors.append(f"Intent model not found: {model_path}")
        return errors
    
    import yaml
    try:
        model = yaml.safe_load(model_path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors
    
    # Check required top-level keys
    required = ["device", "platform", "version", "interfaces", "vrfs", "routing", "peers"]
    for key in required:
        if key not in model:
            errors.append(f"Missing required key: {key}")
    
    # Check peers are objects not parallel lists
    if "peers" in model:
        for peer in model["peers"]:
            if not isinstance(peer, dict):
                errors.append("Peers must be objects, not parallel lists")
            required_peer = ["id", "address", "remote_as", "address_families"]
            for k in required_peer:
                if k not in peer:
                    errors.append(f"Peer missing required field: {k}")
    
    return errors

def check_vendor_templates(template_path: Path) -> list[str]:
    errors = []
    vendors = ["iosxe", "nxos", "eos", "junos"]
    for vendor in vendors:
        vendor_dir = template_path / vendor
        if not vendor_dir.exists():
            errors.append(f"Missing vendor template directory: {vendor}")
            continue
        
        # Check for key templates
        for t in ["interfaces.j2", "bgp.j2", "ospf.j2", "evpn.j2"]:
            if not (vendor_dir / t).exists():
                errors.append(f"Missing template {t} for {vendor}")
    
    return errors

def check_unsupported_handling(template_path: Path) -> list[str]:
    errors = []
    # Check that unsupported features produce structured findings
    for vendor in ["iosxe", "nxos", "eos", "junos"]:
        for t in ["interfaces.j2", "bgp.j2"]:
            tmpl = template_path / vendor / t
            if tmpl.exists():
                content = tmpl.read_text()
                if "unsupported" not in content.lower() and "not supported" not in content.lower():
                    errors.append(f"{vendor}/{t}: no unsupported feature handling")
    
    return errors

def check_mtu_calculation(template_path: Path) -> list[str]:
    errors = []
    # Check for VXLAN MTU calculation
    for vendor in ["iosxe", "nxos", "eos", "junos"]:
        tmpl = template_path / vendor / "interfaces.j2"
        if tmpl.exists():
            content = tmpl.read_text()
            if "vxlan" in content.lower() and "mtu" not in content.lower():
                errors.append(f"{vendor}: VXLAN config missing MTU calculation")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--template-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_intent_model(Path(args.model_path)))
    all_errors.extend(check_vendor_templates(Path(args.template_path)))
    all_errors.extend(check_unsupported_handling(Path(args.template_path)))
    all_errors.extend(check_mtu_calculation(Path(args.template_path)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: network-protocols-as-code validated")