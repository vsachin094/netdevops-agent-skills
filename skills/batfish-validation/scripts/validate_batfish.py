#!/usr/bin/env python3
"""Validate batfish-validation snapshot and queries."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_snapshot_structure(snapshot_path: Path) -> list[str]:
    errors = []
    required = ["configs", "hosts"]
    for d in required:
        if not (snapshot_path / d).exists():
            errors.append(f"Missing required directory: {d}")
    return errors

def check_parse_warnings(snapshot_path: Path) -> list[str]:
    errors = []
    # Run pybatfish parse warning check
    rc, out, err = run_cmd(f"python3 -c \"from pybatfish.client.session import Session; bf=Session(host='localhost'); bf.init_snapshot('{snapshot_path.name}'); warnings=bf.q.parseWarning().answer().frame(); print(len(warnings))\"")
    if rc != 0:
        errors.append(f"Parse warning check failed: {err}")
    return errors

def check_questions(questions_path: Path) -> list[str]:
    errors = []
    if not questions_path.exists():
        errors.append(f"Questions file not found: {questions_path}")
        return errors
    
    required_questions = [
        "bgpSessionCompatibility",
        "undefinedReferences",
        "reachable",
    ]
    
    content = questions_path.read_text()
    for q in required_questions:
        if q not in content:
            errors.append(f"Missing critical question: {q}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-path", required=True)
    parser.add_argument("--questions-path", required=True)
    args = parser.parse_args()
    
    snapshot_path = Path(args.snapshot_path)
    questions_path = Path(args.questions_path)
    all_errors = []
    
    all_errors.extend(check_snapshot_structure(snapshot_path))
    all_errors.extend(check_parse_warnings(snapshot_path))
    all_errors.extend(check_questions(questions_path))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: batfish-validation validated")