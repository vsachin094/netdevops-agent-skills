#!/usr/bin/env python3
"""Validate network-rest-clients timeout, retry, and pagination."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_client_structure(client_path: Path) -> list[str]:
    errors = []
    content = client_path.read_text()
    
    # Check for explicit timeouts
    if "Timeout(" not in content and "timeout=" not in content:
        errors.append("No explicit timeout configuration")
    
    # Check for retry on transient only
    if "retry" in content.lower():
        if "502" not in content and "503" not in content and "504" not in content and "429" not in content:
            errors.append("Retry without specifying transient status codes")
    
    # Check for no retry on non-idempotent
    if "POST" in content or "PATCH" in content:
        if "idempotency" not in content.lower():
            errors.append("POST/PATCH without idempotency key handling")
    
    # Check for pagination
    if "paginate" not in content.lower() and "next" not in content.lower():
        errors.append("No pagination handling")
    
    # Check for token externalization
    if "Bearer" in content and "environ" not in content:
        errors.append("Token not externalized via environment")
    
    return errors

def check_error_normalization(client_path: Path) -> list[str]:
    errors = []
    content = client_path.read_text()
    
    if "raise_for_status" not in content:
        errors.append("No raise_for_status for HTTP error handling")
    
    # Check for request ID preservation
    if "request" not in content.lower() and "correlation" not in content.lower():
        errors.append("No request correlation ID")
    
    return errors

def check_mock_tests(client_path: Path) -> list[str]:
    errors = []
    test_path = client_path.parent / "tests"
    if not test_path.exists():
        errors.append("Missing tests/ directory")
        return errors
    
    # Check for mock test scenarios
    required_scenarios = ["429", "503", "malformed", "timeout", "auth", "duplicate"]
    test_files = list(test_path.glob("*.py"))
    test_content = ""
    for tf in test_files:
        test_content += tf.read_text()
    
    for scenario in required_scenarios:
        if scenario not in test_content:
            errors.append(f"Missing test scenario: {scenario}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-path", required=True)
    args = parser.parse_args()
    
    client_path = Path(args.client_path)
    all_errors = []
    
    all_errors.extend(check_client_structure(client_path))
    all_errors.extend(check_error_normalization(client_path))
    all_errors.extend(check_mock_tests(client_path))
    
    # Run tests
    test_path = client_path.parent / "tests"
    if test_path.exists():
        rc, out, err = run_cmd("pytest tests/ -v", cwd=client_path.parent)
        if rc != 0:
            all_errors.append(f"Tests failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: network-rest-clients validated")