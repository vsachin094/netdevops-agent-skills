#!/usr/bin/env python3
"""Validate netops-data-pipelines schema and cardinality."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_schema(schema_path: Path) -> list[str]:
    errors = []
    if not schema_path.exists():
        errors.append(f"Schema file not found: {schema_path}")
        return errors
    
    content = schema_path.read_text()
    
    # Check for required models
    required_models = ["ArpRecord", "MacRecord", "BgpRecord", "InterfaceRecord"]
    for model in required_models:
        if f"class {model}" not in content:
            errors.append(f"Missing required model: {model}")
    
    # Check for validators
    if "@field_validator" not in content and "@validator" not in content:
        errors.append("No field validators defined")
    
    return errors

def check_normalization(normalize_path: Path) -> list[str]:
    errors = []
    if not normalize_path.exists():
        errors.append(f"Normalization module not found: {normalize_path}")
        return errors
    
    content = normalize_path.read_text()
    
    # Check for MAC normalization
    if "normalize_mac" not in content:
        errors.append("Missing normalize_mac function")
    
    # Check for interface normalization
    if "normalize_interface" not in content:
        errors.append("Missing normalize_interface function")
    
    # Check for IP normalization
    if "normalize_ip" not in content:
        errors.append("Missing normalize_ip function")
    
    return errors

def check_pipeline(pipeline_path: Path) -> list[str]:
    errors = []
    if not pipeline_path.exists():
        errors.append(f"Pipeline module not found: {pipeline_path}")
        return errors
    
    content = pipeline_path.read_text()
    
    # Check for cardinality assertions
    if "assert" not in content and "validate" not in content:
        errors.append("No cardinality assertions in pipeline")
    
    # Check for quarantine output
    if "quarantine" not in content:
        errors.append("No quarantine output for rejected records")
    
    # Check for provenance tracking
    if "provenance" not in content and "lineage" not in content:
        errors.append("No provenance/lineage tracking")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-path", required=True)
    parser.add_argument("--normalize-path", required=True)
    parser.add_argument("--pipeline-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_schema(Path(args.schema_path)))
    all_errors.extend(check_normalization(Path(args.normalize_path)))
    all_errors.extend(check_pipeline(Path(args.pipeline_path)))
    
    # Run tests
    test_path = Path(args.schema_path).parent / "tests"
    if test_path.exists():
        rc, out, err = run_cmd("pytest tests/ -v", cwd=test_path.parent)
        if rc != 0:
            all_errors.append(f"Tests failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: netops-data-pipelines validated")