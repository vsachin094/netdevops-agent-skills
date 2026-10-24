#!/usr/bin/env python3
"""Validate gnmi-snmp-telemetry configurations."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
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
    
    if not isinstance(config, dict):
        errors.append("gnmic config must be a YAML mapping")
        return errors

    inputs = config.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("Missing 'inputs' section")
        return errors
    
    for input_name, input_config in inputs.items():
        if not isinstance(input_config, dict):
            errors.append(f"Input {input_name} must be a YAML mapping")
            continue
        subscriptions = input_config.get("subscription")
        if not isinstance(subscriptions, list):
            errors.append(f"Input {input_name} missing subscription")
            continue
        for sub in subscriptions:
            if not isinstance(sub, dict):
                errors.append(f"Input {input_name} subscription entries must be YAML mappings")
                continue
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
    
    rc, _, err = run_cmd(["promtool", "check", "rules", str(rules_path)])
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
    
    if not isinstance(config, dict):
        errors.append("snmp_exporter generator config must be a YAML mapping")
        return errors

    modules = config.get("modules")
    if not isinstance(modules, dict):
        errors.append("Missing 'modules' section")
        return errors
    
    for module_name, module_config in modules.items():
        if not isinstance(module_config, dict):
            errors.append(f"Module {module_name} must be a YAML mapping")
            continue
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