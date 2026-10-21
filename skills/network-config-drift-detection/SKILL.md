---
name: network-config-drift-detection
description: "Build automated network configuration drift detection with scheduled collection, normalization, diffing, alerting, and automated remediation workflows. Use this skill when network devices must remain compliant with a defined desired state stored in Git."
license: MIT
compatibility: Python 3.10+; Git; vendor collection methods (NETCONF, RESTCONF, SSH); diff tools; optional Batfish; CI scheduler (cron, GitHub Actions, GitLab CI)
---

# Network Config Drift Detection (Intermediate)

Drift detection is a continuous loop: collect → normalize → diff → alert → remediate. The desired state lives in Git; actual state is collected from devices.

## Core Engineering Capabilities

- Schedule configuration collection from devices via NETCONF, RESTCONF, or SSH/CLI.
- Normalize collected configs: strip volatile lines (timestamps, counters, NTP clock-period), sort sections, redact secrets.
- Diff normalized actual state against desired state in Git (unified diff, structured JSON).
- Alert on drift with severity, affected device, section, and diff excerpt.
- Trigger automated remediation for approved drift categories (e.g., NTP server mismatch, description drift) with approval gate.
- Track drift history and compliance trends over time.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never overwrite the last known-good desired state; use immutable timestamped snapshots.
- Use an allow-list of volatile patterns for normalization; never remove security, routing, ACL, or interface lines.
- Normalize only known formatting differences; preserve ordering unless device format is order-insensitive.
- Redact secrets before storing or publishing diffs. Do not rely on HTML escaping as secret protection.
- Record collection failures distinctly from drift; never treat an unreachable device as a deletion.
- Require approval for remediation; auto-remediate only pre-approved, low-risk categories.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Define the device inventory, collection methods, desired state location (Git repo/path), normalization rules, volatile patterns, alert thresholds, and remediation policies.

### Phase 2 (Implementation)

1. **Collection** — Parallel collectors per device type (NETCONF get-config, RESTCONF GET, SSH `show running-config`).
2. **Normalization** — Strip volatile lines, sort lists, redact secrets, canonicalize whitespace.
3. **Diff** — Compare normalized actual vs. desired; produce unified diff and structured JSON.
4. **Alert** — Emit alert with device, severity, diff summary, and link to full diff artifact.
5. **Remediation** — For approved categories, generate remediation config and push via change workflow.

### Phase 3 (Verification)

Test: identical configs (no drift), intentional changes (drift detected), volatile-only changes (ignored), collection failures (alerted separately), secret redaction (verified). Run in CI on schedule and on-demand.

1. Deploy collector to scheduler (cron, GitHub Actions workflow_dispatch).
2. Verify first run creates baseline snapshots.
3. Introduce manual change on device → verify drift detected and alerted.
4. Test remediation workflow end-to-end.

## Production Code / Template Example

### Input / Requirement

Provide device inventory, collection credentials/methods, desired state repo, normalization rules, alert destinations, and remediation approval matrix.

### Output / Generated Code

Return collector modules, normalization engine, diff engine, alert formatter, remediation generator, and scheduler configuration.

```python
# collector/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class CollectionResult:
    device: str
    success: bool
    config: str = ""
    error: str = ""
    timestamp: str = ""

class ConfigCollector(ABC):
    @abstractmethod
    def collect(self, device: dict) -> CollectionResult:
        pass

# collector/netconf.py
from collector.base import ConfigCollector, CollectionResult
from ncclient import manager

class NetconfCollector(ConfigCollector):
    def collect(self, device: dict) -> CollectionResult:
        try:
            with manager.connect(
                host=device["host"],
                port=device.get("port", 830),
                username=device["username"],
                password=device["password"],
                hostkey_verify=True,
                device_params={"name": device["platform"]},
            ) as session:
                config = session.get_config(source="running").data_xml
                return CollectionResult(device=device["name"], success=True, config=config)
        except Exception as e:
            return CollectionResult(device=device["name"], success=False, error=str(e))
```

```python
# normalizer/engine.py
import re
from dataclasses import dataclass

VOLATILE_PATTERNS = [
    r"^! Last configuration change",
    r"^ntp clock-period ",
    r"^! Time: ",
    r"^! Running configuration last done at:",
    r"^Current configuration :",
    r"^Building configuration...",
]

SECRET_PATTERNS = [
    (re.compile(r'(password|secret|key)\s+(\S+)', re.I), '<SECRET>'),
    (re.compile(r'(community)\s+(\S+)', re.I), '<SNMP_COMMUNITY>'),
    (re.compile(r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----.*?-----END \1 PRIVATE KEY-----', re.DOTALL), '<PRIVATE_KEY>'),
]

@dataclass
class NormalizedConfig:
    device: str
    lines: list[str]
    redacted: bool = True

def normalize(config: str, device: str) -> NormalizedConfig:
    lines = config.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    
    # Remove volatile lines
    filtered = [l for l in lines if not any(re.match(p, l) for p in VOLATILE_PATTERNS)]
    
    # Redact secrets
    redacted_lines = []
    for line in filtered:
        for pattern, replacement in SECRET_PATTERNS:
            line = pattern.sub(replacement, line)
        redacted_lines.append(line)
    
    # Sort sections that are order-insensitive (e.g., ACL entries, prefix-lists)
    # This is platform-specific; implement per-vendor
    
    return NormalizedConfig(device=device, lines=redacted_lines)
```

```python
# diff/engine.py
import difflib
from dataclasses import dataclass
from normalizer.engine import NormalizedConfig

@dataclass
class DiffResult:
    device: str
    has_drift: bool
    unified_diff: str
    structured_changes: list[dict]
    collection_error: str = ""

def diff_configs(desired: NormalizedConfig, actual: NormalizedConfig) -> DiffResult:
    if actual.collection_error:
        return DiffResult(
            device=actual.device,
            has_drift=False,
            unified_diff="",
            structured_changes=[],
            collection_error=actual.collection_error
        )
    
    diff = list(difflib.unified_diff(
        desired.lines, actual.lines,
        fromfile=f"desired/{desired.device}",
        tofile=f"actual/{actual.device}",
        lineterm=""
    ))
    
    # Parse structured changes (added/removed/modified sections)
    changes = parse_structured_changes(diff)
    
    return DiffResult(
        device=actual.device,
        has_drift=len(diff) > 0,
        unified_diff="\n".join(diff),
        structured_changes=changes
    )

def parse_structured_changes(diff: list[str]) -> list[dict]:
    """Parse unified diff into structured changes: section, type, content."""
    changes = []
    current_section = None
    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("@@"):
            # Extract section context
            continue
        if line.startswith("+"):
            changes.append({"type": "added", "section": current_section, "content": line[1:]})
        elif line.startswith("-"):
            changes.append({"type": "removed", "section": current_section, "content": line[1:]})
    return changes
```

```python
# alert/formatter.py
def format_alert(diff_result: DiffResult) -> dict:
    severity = "critical" if any(c["type"] in ("added", "removed") for c in diff_result.structured_changes) else "warning"
    return {
        "device": diff_result.device,
        "severity": severity,
        "has_drift": diff_result.has_drift,
        "summary": f"Config drift detected on {diff_result.device}: {len(diff_result.structured_changes)} changes",
        "diff_excerpt": "\n".join(diff_result.unified_diff.splitlines()[:20]),
        "full_diff_url": f"https://git.example.com/drift/{diff_result.device}/latest",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
```

```python
# remediation/generator.py
AUTO_REMEDIATE_CATEGORIES = {
    "ntp_server",
    "syslog_server",
    "snmp_community",
    "banner_motd",
    "description",
}

def generate_remediation(diff_result: DiffResult, desired: NormalizedConfig) -> Optional[str]:
    """Generate remediation config for approved categories only."""
    if not diff_result.has_drift:
        return None
    
    approved_changes = [
        c for c in diff_result.structured_changes
        if any(cat in c.get("section", "").lower() for cat in AUTO_REMEDIATE_CATEGORIES)
    ]
    
    if not approved_changes:
        return None  # Requires manual approval
    
    # Generate config to push (platform-specific)
    return f"# Auto-remediation for {diff_result.device}\n" + "\n".join(
        c["content"] for c in approved_changes if c["type"] == "added"
    )
```

```yaml
# .github/workflows/drift-detection.yml
name: Network Config Drift Detection
on:
  schedule:
    - cron: "0 */6 * * *"  # Every 6 hours
  workflow_dispatch:
    inputs:
      device_filter:
        description: "Device name filter"
        required: false

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run drift detection
        env:
          NETOPS_VAULT_PASSWORD: ${{ secrets.NETOPS_VAULT_PASSWORD }}
        run: |
          python -m drift_detector --inventory inventory.yml --desired-state desired/
      - name: Upload drift reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: drift-reports
          path: drift_reports/
          retention-days: 30
      - name: Alert on drift
        if: failure()
        run: |
          # Send to Alertmanager/Slack/PagerDuty
          curl -X POST "${{ secrets.ALERT_WEBHOOK }}" -d @drift_summary.json
```

## Validation, Linting & Testing Commands

- Test normalization: identical configs, volatile-only, secret-bearing, materially changed.
- Test diff: added/removed/modified sections, reordered order-insensitive sections.
- Test alert formatting: severity mapping, excerpt length, URL generation.
- Test remediation: approved categories generate config, unapproved return None.
- Run `python -m pytest tests/ -v` and `python3 scripts/validate_skills.py`.

## References

- [Python difflib](https://docs.python.org/3/library/difflib.html)
- [ncclient documentation](https://ncclient.readthedocs.io/)
- [GitHub Actions scheduled workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#scheduled-events)

## Offline Execution Contract

Normalization and diff logic works on local fixtures with Python standard library. Without device access, test against saved configs and mark collection/remediation as unverified.

## Architecture & Technical Design Patterns

**Pipeline Stages:**
```
Scheduled Trigger
       │
       ▼
┌─────────────┐
│  Collect    │ ──► CollectionResult (success/error)
└─────────────┘
       │
       ▼
┌─────────────┐
│  Normalize  │ ──► NormalizedConfig (volatile stripped, secrets redacted)
└─────────────┘
       │
       ▼
┌─────────────┐
│    Diff     │ ──► DiffResult (unified_diff, structured_changes)
└─────────────┘
       │
       ▼
┌─────────────┐
│   Alert     │ ──► AlertManager/Slack/PagerDuty + artifact upload
└─────────────┘
       │
       ▼
┌─────────────┐
│ Remediate   │ (approved categories only) ──► Change workflow
└─────────────┘
```

**Normalization Rules (Per Vendor):**

| Vendor | Volatile Patterns | Order-Insensitive Sections |
|--------|------------------|----------------------------|
| IOS/IOS-XE | `ntp clock-period`, `! Time:`, `! Last config` | ACL entries, prefix-lists, route-maps |
| NX-OS | `! Time:`, `! Last config`, checkpoint headers | ACL entries, prefix-lists, class-maps |
| EOS | `! Time:`, `! Last config` | ACL entries, prefix-lists, route-maps |
| Junos | `## Last commit`, `## Last changed` | policy-statement terms, prefix-lists, firewall filters |

**Drift Categories:**

| Category | Severity | Auto-Remediate | Examples |
|----------|----------|----------------|----------|
| Security | Critical | No | AAA, SSH, ACL, crypto keys |
| Routing | Critical | No | BGP, OSPF, static routes, VRF |
| Interfaces | High | No | IP, MTU, VLAN, bonding |
| Monitoring | Medium | Yes | NTP, syslog, SNMP, description |
| Cosmetic | Low | Yes | banner, hostname, alias |

**Related Skills:**

- [config-diff-audit](config-diff-audit.md) — Diff engine and normalization patterns
- [config-scrubber](config-scrubber.md) — Secret redaction before diff storage
- [network-change-runbooks](network-change-runbooks.md) — Remediation workflow integration
- [gitops-network-automation](gitops-network-automation.md) — Desired state in Git
- [network-testing-framework](network-testing-framework.md) — Test drift detection in CI
- [cli-tool-packaging](cli-tool-packaging.md) — Package detector as CLI tool