---
name: config-diff-audit
description: "[Tier: Basic] Build Python configuration backup and audit workflows using pathlib, difflib, and optional GitPython, with deterministic noise removal and HTML or unified diffs. Use this skill when tracking device configuration drift or reviewing changes over time."
license: MIT
compatibility: Python 3.10+; Python standard library; optional GitPython and Jinja2; approved device transport or backup source
---

# Configuration Diff Audit (Basic)

Make configuration history useful to an operator. A diff should highlight
intentional control-plane changes, not timestamps, counters, generated keys,
or command prompts that change every collection cycle.

## Core Engineering Capabilities

- Pull or ingest running configurations, normalize line endings, and store
  timestamped artifacts with device identity and source metadata.
- Strip explicitly documented volatile lines before comparison while retaining
  the raw artifact under the approved retention policy.
- Generate unified or HTML diffs, commit reviewed snapshots to Git, and emit a
  structured audit record for CI or ticketing systems.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never overwrite the last known-good snapshot; use immutable timestamped files
  and atomic writes.
- Use an allow-list of noise patterns for uptime, timestamps, counters, and
  generated metadata. Never remove security, routing, ACL, or interface lines
  merely because they look dynamic.
- Normalize only known formatting differences and preserve ordering unless the
  device format is explicitly order-insensitive.
- Redact secrets before storing or publishing diffs. Do not rely on HTML
  escaping as secret protection.
- Record collection failures distinctly from an empty configuration and never
  treat an unreachable device as a deletion.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Identify the source, device key, retention policy, and canonical filename.
2. Collect or load raw configuration and validate that it is not an error page,
   login prompt, or truncated response.
3. Apply versioned normalization and redaction, then calculate the diff.
4. Store raw/normalized artifacts according to policy and publish the review
   diff with exit status reflecting drift and collection errors.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
import difflib
from pathlib import Path

VOLATILE = ("! Last configuration change", "ntp clock-period ")

def stable_lines(text: str) -> list[str]:
    return [line for line in text.replace("\r\n", "\n").splitlines()
            if not line.startswith(VOLATILE)]

diff = difflib.unified_diff(stable_lines(old), stable_lines(new), fromfile="old", tofile="new")
Path("audit.diff").write_text("\n".join(diff) + "\n", encoding="utf-8")
```

## Validation, Linting & Testing Commands

- Test identical configs, intended changes, volatile-only changes, truncation,
  empty output, and secret redaction.
- Ensure Git commits contain the normalized artifact and metadata, not secrets.
- Review the first run manually before enabling alerting.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Python `difflib`](https://docs.python.org/3/library/difflib.html)
- [GitPython documentation](https://gitpython.readthedocs.io/)

## Offline Execution Contract

The diff and normalization workflow works on local fixtures with the Python standard library. Without Git or device access, produce deterministic unified diffs and distinguish missing collection from unchanged configuration.

## Architecture & Technical Design Patterns

Use a pipeline with immutable stages: `raw -> validated -> scrubbed ->
normalized -> diff -> published`. Validate that a collected file contains a
device config marker and is not a login prompt, command error, or truncated
response before replacing a snapshot. Keep raw and normalized artifacts
separate when policy allows.

Noise removal must be an allow-list of exact patterns, for example timestamps,
`ntp clock-period`, generated comments, and known byte counters. Compile the
patterns with `re.MULTILINE`, preserve line order, and record which rules were
applied. Use `difflib.unified_diff(old, new, fromfile=device/old,
tofile=device/new, lineterm="")`; a changed normalized file means drift,
while a collection exception means unknown state. Commit only after redaction
and use a stable device filename to avoid duplicate history.
