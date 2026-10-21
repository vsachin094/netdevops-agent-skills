---
name: nso-device-onboarding
description: "[Tier: Basic] Automate Cisco NSO device onboarding through CLI, RESTCONF, or Python, including authgroups, NED assignment, device groups, SSH host keys, sync-from, check-sync, and compare-config. Use this skill when adding or validating managed devices in an NSO inventory."
license: MIT
compatibility: Cisco NSO with compatible NED packages; Python/RESTCONF optional; device credentials and management reachability supplied securely
---

# NSO Device Onboarding (Basic)

Onboard a device as a controlled lifecycle: identity, credentials, NED
compatibility, reachability, SSH trust, synchronization, and verification.

## Core Engineering Capabilities

- Create authgroups and device records with address, port, platform, NED,
  device group, and management metadata.
- Fetch SSH host keys, sync from the device, check sync, compare config, and
  produce an operator-readable onboarding report.
- Use dry-run or check operations before committing NSO database changes.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never place passwords or private keys in scripts, service models, logs, or
  examples. Use NSO secrets and approved external credential mechanisms.
- Verify NED package/version compatibility before assigning a device. Do not
  assume a similarly named NED supports the target release.
- Treat `fetch-ssh-host-keys` as an explicit trust action; validate management
  address and host identity before accepting keys.
- Run `commit dry-run outformat native` before every onboarding commit and
  inspect the generated device-native impact.
- Run `sync-from`, `check-sync`, and `compare-config`; distinguish an empty
  device from a failed or unauthorized sync.
- Make re-running onboarding idempotent and report conflicts rather than
  overwriting an existing device with different identity data.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Record the NSO version, device address and auth source, NED package and version, protocol, authgroup, device type, and sync-from policy. Confirm whether the device is reachable and whether onboarding may alter it.

### Phase 2 (Implementation)

Generate a repeatable onboarding sequence that creates the device, assigns the NED and authgroup, commits the candidate, and runs connect/sync verification. Keep device credentials external and make partial onboarding recoverable.

### Phase 3 (Verification)

Test duplicate onboarding, invalid NED, unreachable device, auth failure, failed commit, and sync mismatch in a lab or fixture-backed environment. Capture NSO transaction output without leaking secrets.

1. Validate inventory, credentials, NED, device group, and reachability.
2. Create or reconcile authgroup and device metadata.
3. Fetch/verify SSH keys, dry-run, commit, and sync-from.
4. Check sync and compare config; record failures and remediation steps.

## Production Code / Template Example

### Input / Requirement

Provide device metadata, NED package, authgroup reference, protocol, address, onboarding scope, and the expected sync-from or rollback behavior.

### Output / Generated Code

Return the NSO commands or package artifacts, prechecks, postchecks, failure recovery, and a verification transcript suitable for operator review.


```text
devices device edge-1
 address 192.0.2.10
 device-type cli ned-id cisco-iosxr
 authgroup lab-auth
 device-group edge
 state unlocked
```

The exact NSO model syntax depends on the installed release and NED; render it
from the target schema and verify with dry-run before applying.

## Validation, Linting & Testing Commands

- Test new, existing, conflicting, unreachable, wrong-NED, and out-of-sync
  devices in a lab NSO instance.
- Verify SSH host-key trust and no secret leakage in reports.
- Run `python3 scripts/validate_skills.py`.

## References

- [NSO device manager](https://nso-docs.cisco.com/guides/nso-6.1/operation-and-usage/operations/nso-device-manager)
- [NSO lifecycle operations](https://nso-docs.cisco.com/guides/nso-6.5/operation-and-usage/operations/lifecycle-operations)

## Offline Execution Contract

Generate inventory, dry-run commands, and onboarding checklists from local NSO/NED schemas or supplied fixtures. Without NSO, NEDs, or devices, do not claim host-key, sync, or NED compatibility verification.

## Architecture & Technical Design Patterns

An onboarding record should contain `name`, management address/port,
`authgroup`, `ned_id`, `device_group`, `admin_state`, and a credential
reference—not a password. Reconciliation is keyed by device name and must
detect an existing device whose address or NED differs from desired state.

Operational sequence: validate reachability and NED package, create/reconcile
authgroup and device metadata, run `devices fetch-ssh-host-keys`, inspect the
trust decision, perform `commit dry-run outformat native`, commit only after
approval, then run `devices sync-from`, `devices check-sync`, and
`devices device <name> compare-config`. A sync failure, auth failure, and
out-of-sync result are different remediation paths. For bulk onboarding,
serialize trust decisions and report each device independently.
