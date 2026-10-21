---
name: config-diff-audit
description: "Build Python configuration backup and audit workflows using pathlib, difflib, and optional GitPython, with deterministic noise removal and HTML or unified diffs. Use this skill when tracking device configuration drift or reviewing changes over time."
license: MIT
compatibility: Python 3.10+; Python standard library; optional GitPython and Jinja2; approved device transport or backup source
---

# Configuration Diff Audit (Basic)

Make configuration history useful to an operator. A diff should highlight intentional control-plane changes, not timestamps, counters, generated keys, or command prompts that change every collection cycle.

## Core Engineering Capabilities

- Pull or ingest running configurations, normalize line endings, and store timestamped artifacts with device identity and source metadata.
- Strip explicitly documented volatile lines before comparison while retaining the raw artifact under the approved retention policy.
- Generate unified or HTML diffs, commit reviewed snapshots to Git, and emit a structured audit record for CI or ticketing systems.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never overwrite the last known-good snapshot; use immutable timestamped files and atomic writes.
- Use an allow-list of noise patterns for uptime, timestamps, counters, and generated metadata. Never remove security, routing, ACL, or interface lines merely because they look dynamic.
- Normalize only known formatting differences and preserve ordering unless the device format is explicitly order-insensitive.
- Redact secrets before storing or publishing diffs. Do not rely on HTML escaping as secret protection.
- Record collection failures distinctly from an empty configuration and never treat an unreachable device as a deletion.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Identify the configuration source, capture timestamp, device identity, normalization rules, secret handling, and files or sections that are intentionally noisy. Decide whether line order is meaningful before comparing snapshots.

### Phase 2 (Implementation)

Generate a deterministic capture and diff workflow that normalizes only approved noise, preserves evidence, and produces both machine-readable and reviewer-friendly output. Never hide a change merely because it is inconvenient to compare.

### Phase 3 (Verification)

Compare identical, reordered, secret-bearing, and materially changed snapshots. Confirm the scrubber and diff filters do not erase an ACL, route, credential reference, or device-context change.

1. Identify the source, device key, retention policy, and canonical filename.
2. Collect or load raw configuration and validate that it is not an error page, login prompt, or truncated response.
3. Apply versioned normalization and redaction, then calculate the diff.
4. Store raw/normalized artifacts according to policy and publish the review diff with exit status reflecting drift and collection errors.

## Production Code / Template Example

### Input / Requirement

Provide baseline and candidate configurations, device metadata, approved ignore patterns, redaction rules, and the required diff format.

### Output / Generated Code

Return normalized snapshots, a diff report, the filter configuration, and regression fixtures proving meaningful changes remain visible.

```python
import difflib
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DiffResult:
    device: str
    changed: bool
    diff: str
    collection_error: Optional[str] = None

VOLATILE_PATTERNS = [
    r"^! Last configuration change",
    r"^ntp clock-period ",
    r"^! Time: ",
    r"^! Running configuration last done at:",
]

def stable_lines(text: str) -> List[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.splitlines():
        if not any(re.match(p, line) for p in VOLATILE_PATTERNS):
            lines.append(line)
    return lines

def diff_configs(old: str, new: str, device: str) -> DiffResult:
    old_lines = stable_lines(old)
    new_lines = stable_lines(new)
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"{device}/old", tofile=f"{device}/new", lineterm=""))
    return DiffResult(device=device, changed=len(diff) > 0, diff="\n".join(diff))

def collect_and_audit(device: str, transport) -> DiffResult:
    try:
        raw = transport.get_running_config()
        if not raw or "Error" in raw or "login:" in raw.lower():
            return DiffResult(device=device, changed=False, diff="", collection_error="invalid config collected")
        baseline_path = Path(f"snapshots/{device}/baseline.cfg")
        if baseline_path.exists():
            baseline = baseline_path.read_text()
            return diff_configs(baseline, raw, device)
        else:
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(raw)
            return DiffResult(device=device, changed=False, diff="", collection_error="baseline created")
    except Exception as e:
        return DiffResult(device=device, changed=False, diff="", collection_error=str(e))
```

```bash
# Run audit
python3 -m config_diff_audit --inventory inventory.yml --output audit.json
```

## Validation, Linting & Testing Commands

- Test identical configs, intended changes, volatile-only changes, truncation, empty output, and secret redaction.
- Ensure Git commits contain the normalized artifact and metadata, not secrets.
- Review the first run manually before enabling alerting.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Python `difflib`](https://docs.python.org/3/library/difflib.html)
- [GitPython documentation](https://gitpython.readthedocs.io/)

## Offline Execution Contract

The diff and normalization workflow works on local fixtures with the Python standard library. Without Git or device access, produce deterministic unified diffs and distinguish missing collection from unchanged configuration.

## Architecture & Technical Design Patterns

Use a pipeline with immutable stages: `raw -> validated -> scrubbed -> normalized -> diff -> published`. Validate that a collected file contains a device config marker and is not a login prompt, command error, or truncated response before replacing a snapshot. Keep raw and normalized artifacts separate when policy allows.

Noise removal must be an allow-list of exact patterns, for example timestamps, `ntp clock-period`, generated comments, and known byte counters. Compile the patterns with `re.MULTILINE`, preserve line order, and record which rules were applied. Use `difflib.unified_diff(old, new, fromfile=device/old, tofile=device/new, lineterm="")`; a changed normalized file means drift, while a collection exception means unknown state. Commit only after redaction and use a stable device filename to avoid duplicate history.