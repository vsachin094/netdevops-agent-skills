---
name: asa-config-backup-restore
description: "[Tier: Intermediate] Back up, verify, restore, and roll back Cisco ASA running/startup configurations with credential isolation, pre/post checks, change evidence, and idempotent per-device execution. Use this skill when firewall configurations must be captured on a schedule, validated before restore, and recoverable with auditable evidence."
license: MIT
compatibility: Cisco ASA with SSH or HTTP/HTTPS API access; Python 3.9+; Netmiko or requests; persistent credential store (env vars or ansible-vault); lab or maintenance-window ASA for restore testing
---

# ASA Config Backup & Restore (Intermediate)

Capture ASA configurations on a schedule, verify integrity before restore, and recover from bad changes with rollback evidence.

## Core Engineering Capabilities

- Back up running-config and startup-config from ASA over SSH (Netmiko) or the ASA API, timestamped and stored with device, date, and checksum.
- Verify backup integrity: checksum comparison, config completeness (presence of `failover`, `access-list`, `nat`, `policy-map`, `tunnel-group` blocks as applicable), and diff against the previous backup.
- Pre-check before restore: device reachability, config mode availability, storage space, failover/standby state, and active-session impact assessment.
- Restore with verification: apply config, confirm `copy running-config startup-config`, validate key blocks post-restore, and run connectivity/ACL postchecks.
- Rollback: revert to the previous known-good backup on postcheck failure, with change evidence (before/after configs, diffs, timestamps, operator).
- Credential isolation: secrets from env vars or ansible-vault; never hardcode enable passwords, pre-shared keys, or certificates.
- Idempotent per-device execution: skip unchanged configs, record per-device status, duration, and result in JSON Lines.

## Architecture & Technical Design Patterns

```
inventory + credentials + backup schedule
                    │
                    ▼
          SSH/API connect → show run → store
                    │
                    ▼
        checksum + completeness + diff vs previous
                    │
                    ▼
   pre-check → restore → postcheck → rollback gate
                    │
                    ▼
          evidence bundle (diff, timestamps, status)
```

Keep backups in a dated, append-only store (e.g., `backups/<device>/<YYYYMMDD>-<sha>.cfg`) so restoration is deterministic. Maintain a manifest mapping device → latest known-good backup. Separate the backup reader (no mutation) from the restorer (mutation, gated by pre-check and approval).

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never hardcode enable passwords, pre-shared keys, certificates, or any secret in source, backups, logs, or prompts. Read from env vars or ansible-vault-compatible encrypted files.
- Treat restore as a state-changing operation: require pre-check, capture the current config before overwrite, and define an automatic rollback trigger (postcheck failure).
- Confirm failover/standby state before restoring; restoring only the active unit while standby is out of sync can cause traffic disruption on failover.
- Validate that `access-list`, `nat`, `tunnel-group`, and `policy-map` blocks survive restore; an incomplete restore can silently break VPNs and traffic filtering.
- Do not parse ASA output with positional string splits; use structured comparison (diff) and block presence checks. Preserve raw config only under approved retention.
- Test backup/restore in a lab or maintenance window first. ASA behavior (ROMMON, failover, context mode, ASAv vs physical) varies by version and platform; do not claim cross-version support without lab evidence.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: ASA inventory (host, version, context mode, failover role), credential source, backup transport (SSH/API), schedule, storage location, pre-check items, postcheck commands, rollback trigger, and evidence retention policy.

### Phase 2 (Implementation)

Implement backup (show running-config/store with checksum), integrity verification, pre-check, restore, postcheck, and rollback. Gate restore behind pre-check and a stored pre-restore config snapshot.

### Phase 3 (Verification)

Run backup → checksum → diff vs previous. Run restore in lab → postcheck (key blocks present, VPN tunnels up, ACL behavior) → assert rollback fires on failure. Record evidence bundle per run.

### Input / Requirement

ASA device reachable over SSH/API; credentials; backup storage path; pre-check and postcheck command list; rollback policy.

### Output / Generated Code

Timestamped, checksummed backup files; per-run JSON Lines result; before/after diffs; rollback evidence on failure.

## Production Code / Template Example

```python
# Illustrative backup skeleton (values are examples, not defaults)
from netmiko import ConnectHandler
import hashlib
from pathlib import Path

def backup_asa(device: dict, store: Path) -> dict:
    store.mkdir(parents=True, exist_ok=True)
    with ConnectHandler(**device) as conn:
        running = conn.send_command("show running-config")
    digest = hashlib.sha256(running.encode()).hexdigest()[:16]
    path = store / f"{device['host']}-{digest}.cfg"
    path.write_text(running)
    return {"device": device["host"], "path": str(path), "sha256": digest, "bytes": len(running)}
```

## Validation, Linting & Testing Commands

- `python -m compileall` plus `ruff check` / `mypy` on backup/restore Python modules.
- Unit tests with mocked SSH/API: backup storage, checksum, completeness check, diff, pre-check pass/fail, restore, postcheck failure → rollback.
- Integrity test: corrupt a backup copy and confirm the checksum/completeness check rejects it.
- Restore test against a lab/ASAv in a maintenance window: capture pre config, apply backup, verify key blocks, trigger rollback on injected postcheck failure.
- Credential redaction: grep logs/output for secrets — must not appear.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Cisco ASA command reference](https://www.cisco.com/c/en/us/support/docs/security/asa-firepower-asa/)
- [Netmiko Cisco ASA platform notes](https://ktbyers.github.io/netmiko/)

## Offline Execution Contract

Backup reading and diff logic can be unit-tested offline with mocked SSH/API fixtures. Live backup, restore, and failover testing require an ASA (physical or ASAv) in a lab or maintenance window; mark cross-version behavior unverified until lab-tested.

## Related Skills

- [netmiko-core](../netmiko-core/SKILL.md) — SSH transport and per-device result aggregation used by backup/restore
- [network-change-runbooks](../network-change-runbooks/SKILL.md) — pre/post checks and rollback for firewall changes
- [config-diff-audit](../config-diff-audit/SKILL.md] — diff and audit of configuration changes
