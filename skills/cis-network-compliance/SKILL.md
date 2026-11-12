---
name: cis-network-compliance
description: "[Tier: Intermediate] Scan network device configurations against CIS benchmarks — identify non-compliant settings, generate remediation commands, track compliance drift over time, and produce audit-ready evidence. Use this skill when firewalls, switches, and routers must meet CIS security configuration baselines."
license: MIT
compatibility: Python 3.9+; network device configs (Cisco IOS/NX-OS, Juniper Junos, Arista EOS, Palo Alto PAN-OS); CIS benchmark text or JSON; optional Osquery or custom scanner; lab devices for validation
---

# CIS Network Compliance (Intermediate)

Scan network device configurations against CIS security benchmarks and produce remediation plans and audit evidence.

## Core Engineering Capabilities

- Parse running-configs from Cisco IOS/NX-OS, Juniper Junos, Arista EOS, Palo Alto PAN-OS, and other network devices.
- Compare device settings against CIS benchmark requirements (SNMP, SSH, logging, banners, NTP, password policy, unused services, access control lists).
- Classify findings as pass/fail/manual-review with CIS rule IDs, severity, and device context.
- Generate remediation commands (CLI snippets) for each failed check.
- Track compliance drift over time: compare current scan against previous baseline and flag regressions.
- Produce audit-ready evidence: scan timestamp, device inventory, CIS version, pass/fail counts, and remediation status.
- Integrate with config backups and change management so remediations are tracked as tickets.

## Architecture & Technical Design Patterns

```
device configs (backups / live collect)
                │
                ▼
      config parser per platform
                │
                ▼
   CIS rule engine (pattern + logic match)
                │
                ▼
   findings: pass / fail / manual-review
                │
                ▼
   remediation commands + drift vs baseline
                │
                ▼
   audit report + ticket creation
```

Keep CIS benchmark rules in separate YAML/JSON files per platform and benchmark version so updates don't require code changes. Store scan results in a time-series or append-only store for drift comparison. Separate the scanner (read-only) from the remediator (write, requires approval).

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Do not treat automated CIS scanning as a substitute for manual audit; some CIS controls require human judgment (e.g., "appropriate logging destination" depends on business context).
- Do not hardcode CIS rule thresholds, passwords, or community strings; parameterize them per environment.
- Remediation commands must be reviewed and tested in lab before applying to production; an incorrect ACL or SSH change can lock you out of a device.
- Validate that scanner output matches actual device behavior — a missing `no service pad` line in the config may mean the default is already secure, not a failure.
- Store scan reports and evidence in a tamper-evident location (WORM storage, signed artifacts, or Git with signed commits).
- Confirm the CIS benchmark version matches the device OS version; CIS Cisco IOS v1.5 does not apply the same way to IOS-XE 17.x.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: device inventory and OS versions, CIS benchmark version per platform, config collection method (backup files or live SSH), scan frequency, remediation approval process, evidence storage location, and exception handling for manual-review controls.

### Phase 2 (Implementation)

Implement config parsers per platform, encode CIS rules as data files, build the rule engine, generate remediation commands, and set up drift comparison against previous scans.

### Phase 3 (Verification)

Run the scanner against known-good and known-bad config fixtures and confirm findings match expected CIS rule IDs. Verify drift detection by scanning the same device twice with a intentional change between scans. Confirm remediation commands apply cleanly in lab without breaking connectivity.

### Input / Requirement

Network device configurations, CIS benchmark definitions per platform, scan schedule, evidence storage, remediation approval workflow.

### Output / Generated Code

Scanner code, CIS rule data files, scan reports (JSON/HTML), remediation command lists, drift reports, and audit evidence bundles.

## Production Code / Template Example

```python
# Scan a Cisco IOS config against selected CIS rules (illustrative values)
import re
from pathlib import Path

def scan_cisco_ios(config_text: str) -> list[dict]:
    findings = []
    # CIS 1.1: Ensure no unused services are enabled
    if re.search(r"^\s*service pad", config_text, re.MULTILINE):
        findings.append({
            "rule_id": "1.1",
            "title": "Disable unused service pad",
            "severity": "low",
            "status": "fail",
            "remediation": "no service pad",
        })
    # CIS 2.3: Ensure SSH version 2 is configured
    if not re.search(r"ip ssh version 2", config_text):
        findings.append({
            "rule_id": "2.3",
            "title": "Configure SSH version 2",
            "severity": "high",
            "status": "fail",
            "remediation": "ip ssh version 2",
        })
    return findings

# Example usage:
# config = Path("backups/core-sw-01.cfg").read_text()
# results = scan_cisco_ios(config)
```

## Validation, Linting & Testing Commands

- `python -m compileall` plus `ruff check` / `mypy` on scanner modules.
- Unit tests with fixture configs: known-good config passes all rules; known-bad config triggers correct rule IDs and remediations.
- Drift test: scan same config twice with one intentional change; confirm drift report shows exactly one new failure.
- Lab test: apply remediation commands to a lab device, re-scan, and confirm the finding moves from fail to pass.
- `python3 scripts/validate_skills.py` from the repository root.

## References

- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [CIS Cisco IOS Benchmark](https://www.cisecurity.org/benchmark/cisco_ios)
- [CIS Juniper Junos Benchmark](https://www.cisecurity.org/benchmark/juniper_junos)
- [NIST SP 800-41 Rev. 1 (Firewalls)](https://csrc.nist.gov/publications/detail/sp/800-41/rev-1/final)

## Offline Execution Contract

Rule authoring, scanner code review, and fixture-based unit testing require no live devices. Live scanning against production devices requires config collection access; mark benchmark version coverage unverified until validated against the target device OS.

## Related Skills

- [cisco-asa-config-backup-restore](../cisco-asa-config-backup-restore/SKILL.md) — firewall configs that feed compliance scans
- [config-diff-audit](../config-diff-audit/SKILL.md) — diff and audit that complements compliance drift detection
- [network-config-drift-detection](../network-config-drift-detection/SKILL.md) — general drift detection alongside CIS-specific scans
