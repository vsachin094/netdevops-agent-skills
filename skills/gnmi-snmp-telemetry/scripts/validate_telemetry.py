#!/usr/bin/env python3
"""Validate gnmi-snmp-telemetry configurations."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_gnmic_config(config_path: Path) -> list[str]:
    errors = []
    if not config_path.exists():
        errors.append(f"gnmic config not found: {config_path}")
        return errors
    
    # Validate YAML structure
    import yaml
    try:
        config = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors
    
    if "inputs" not in config:
        errors.append("Missing 'inputs' section")
    
    for input_name, input_config in config.get("inputs", {}).items():
        if "subscription" not in input_config:
            errors.append(f"Input {input_name} missing subscription")
        for sub in input_config.get("subscription", []):
            if "path" not in sub:
                errors.append("Subscription missing path")
            if "mode" not in sub:
                errors.append("Subscription missing mode (SAMPLE/ON_CHANGE)")
    
    return errors

def check_promql_rules(rules_path: Path) -> list[str]:
    errors = []
    if not rules_path.exists():
        errors.append(f"PromQL rules not found: {rules_path}")
        return errors
    
    rc, out, err = run_cmd(f"promtool check rules {rules_path}")
    if rc != 0:
        errors.append(f"promtool check failed: {err}")
    
    return errors

def check_snmp_exporter_generator(config_path: Path) -> list[str]:
    errors = []
    if not config_path.exists():
        errors.append(f"snmp_exporter generator config not found: {config_path}")
        return errors
    
    import yaml
    try:
        config = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors
    
    if "modules" not in config:
        errors.append("Missing 'modules' section")
    
    for module_name, module_config in config.get("modules", {}).items():
        if "walk" not in module_config:
            errors.append(f"Module {module_name} missing walk")
        if "metric_prefix" not in module_config:
            errors.append(f"Module {module_name} missing metric_prefix")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--gnmic-config", required=True)
    parser.add_argument("--promql-rules", required=True)
    parser.add_argument("--snmp-generator", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_gnmic_config(Path(args.gnmic_config)))
    all_errors.extend(check_promql_rules(Path(args.promql_rules)))
    all_errors.extend(check_snmp_exporter_generator(Path(args.snmp_generator)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: gnmi-snmp-telemetry validated")