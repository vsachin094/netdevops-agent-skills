#!/usr/bin/env bash
set -euo pipefail
command -v ansible-lint >/dev/null 2>&1 || { echo "ERROR: ansible-lint is required" >&2; exit 2; }
ansible-lint --profile production "$@"
