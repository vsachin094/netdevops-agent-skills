#!/usr/bin/env python3
"""Validate nso-xml-templates package structure."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def check_package_structure(pkg_path: Path) -> list[str]:
    errors = []
    required = [
        "package-meta-data.xml",
        "src/yang",
        "templates",
    ]
    for f in required:
        if not (pkg_path / f).exists():
            errors.append(f"Missing required file/dir: {f}")
    
    # Check for python directory if callbacks exist
    if (pkg_path / "python").exists():
        if not (pkg_path / "src" / "yang").exists():
            errors.append("Python package missing YANG model")
    
    return errors

def check_template_structure(template_path: Path) -> list[str]:
    errors = []
    if not template_path.exists():
        errors.append(f"Templates directory not found: {template_path}")
        return errors
    
    # Check for processing instructions
    for tmpl in template_path.glob("*.xml"):
        content = tmpl.read_text()
        if "<?if" in content and "<?end?>" not in content:
            errors.append(f"Unclosed processing instruction in {tmpl.name}")
    
    # Check for leafrefs in YANG
    yang_files = list((pkg_path / "src" / "yang").glob("*.yang")) if (pkg_path / "src" / "yang").exists() else []
    for yang in yang_files:
        content = yang.read_text()
        if "leafref" in content and "require-instance" not in content:
            errors.append(f"leafref without require-instance in {yang.name}")
    
    return errors

def check_dry_run(pkg_path: Path) -> list[str]:
    errors = []
    # Check if dry-run works
    rc, out, err = run_cmd("ncs-make-package --compile --dry-run", cwd=pkg_path)
    if rc != 0:
        errors.append(f"Dry-run compile failed: {err}")
    
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg-path", required=True)
    args = parser.parse_args()
    
    all_errors = []
    all_errors.extend(check_package_structure(Path(args.pkg_path)))
    all_errors.extend(check_template_structure(Path(args.pkg_path)))
    all_errors.extend(check_dry_run(Path(args.pkg_path)))
    
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    else:
        print("OK: nso-xml-templates validated")