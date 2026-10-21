#!/usr/bin/env bash
set -euo pipefail
command -v terraform >/dev/null 2>&1 || { echo "ERROR: terraform is required" >&2; exit 2; }
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
