#!/usr/bin/env python3
"""Validate async-netops concurrency and error handling."""

import asyncio
import sys
from pathlib import Path

def check_concurrency_limits(code_path: Path) -> list[str]:
    errors = []
    content = code_path.read_text()
    
    if "Semaphore" not in content and "max_workers" not in content:
        errors.append("No concurrency limit found (Semaphore or max_workers)")
    
    if "gather" in content and "return_exceptions" not in content:
        errors.append("asyncio.gather without return_exceptions=True")
    
    if "wait_for" not in content and "timeout" not in content:
        errors.append("No timeout handling found")
    
    return errors

def check_error_handling(code_path: Path) -> list[str]:
    errors = []
    content = code_path.read_text()
    
    if "CancelledError" not in content:
        errors.append("No CancelledError handling (required for graceful shutdown)")
    
    if "finally:" not in content:
        errors.append("No finally block for cleanup")
    
    if "except Exception" in content and "except asyncio.CancelledError" not in content:
        errors.append("Bare except Exception will catch CancelledError")
    
    return errors

def check_result_schema(code_path: Path) -> list[str]:
    errors = []
    content = code_path.read_text()
    
    required_fields = ["device", "status", "error", "duration"]
    for field in required_fields:
        if field not in content:
            errors.append(f"Result schema missing field: {field}")
    
    return errors

async def run_tests():
    # Import and run the module's tests
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-path", required=True)
    args = parser.parse_args()
    
    code_path = Path(args.code_path)
    all_errors = []
    
    all_errors.extend(check_concurrency_limits(code_path))
    all_errors.extend(check_error_handling(code_path))
    all_errors.extend(check_result_schema(code_path))
    
    # Run pytest if tests exist
    import subprocess
    test_path = code_path.parent / "tests"
    if test_path.exists():
        rc, out, err = subprocess.run("pytest tests/ -v", shell=True, capture_output=True, text=True, cwd=code_path.parent)
        if rc != 0:
            all_errors.append(f"Tests failed: {err}")
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: async-netops validated")