#!/usr/bin/env bash
set -euo pipefail
command -v terraform >/dev/null 2>&1 || { echo "ERROR: terraform required" >&2; exit 2; }
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
command -v tflint >/dev/null 2>&1 && tflint --init && tflint || true
command -v checkov >/dev/null 2>&1 && checkov -d . || true
