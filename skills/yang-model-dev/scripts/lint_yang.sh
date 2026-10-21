#!/usr/bin/env bash
set -euo pipefail
if ! command -v pyang >/dev/null 2>&1; then
  echo "ERROR: pyang is required" >&2
  exit 2
fi
pyang --strict --lint "$@"
