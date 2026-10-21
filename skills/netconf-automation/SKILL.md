---
name: netconf-automation
description: "[Tier: Advanced] Build model-driven NETCONF automation with ncclient, including capability negotiation, namespace-safe filters, candidate and running datastores, locks, validate, commit, confirmed commit, rollback, and notifications. Use this skill when a device exposes NETCONF and the workflow must change configuration transactionally rather than by CLI scraping."
license: MIT
compatibility: Python 3.10+; ncclient 0.6.15+; NETCONF RFC 6241/6242; YANG modules and device capability output; pytest
---

# NETCONF Automation (Advanced)

Treat NETCONF as a transaction protocol with a schema contract. A successful
SSH session or RPC reply does not prove that the requested configuration was
accepted, committed, or operationally realized on the device.

## Core Engineering Capabilities

- Negotiate and record device capabilities, NETCONF base version, datastores,
  candidate, validate, confirmed-commit, rollback, and notification support.
- Build namespace-correct subtree or XPath filters from supplied YANG modules
  and list keys; never derive paths from CLI names.
- Read running or intended configuration, calculate a reviewable diff, and
  apply edits with explicit `merge`, `replace`, `create`, `delete`, or
  `remove` semantics.
- Use candidate locking, `edit-config`, `validate`, commit, confirmed commit,
  cancel-commit, discard-changes, and unlock in a bounded transaction.
- Map `rpc-error` details into actionable failures without hiding error type,
  error-tag, error-path, or error-message.
- Subscribe to supported notifications and close subscriptions cleanly when
  the workflow or timeout ends.

## Architecture & Technical Design Patterns

Separate model construction, transport, transaction control, and postchecks:

```text
YANG modules + desired intent + capabilities
                    │
                    ▼
       namespace-safe payload/filter
                    │
                    ▼
    connect → lock → edit → validate → commit
                    │                  │
                    │                  ▼
                    │          confirmed commit
                    ▼                  │
              postcondition ← cancel/confirm
```

Use a capability-driven transaction. If the device does not advertise
`candidate`, do not silently switch to direct `running` edits; require an
explicit operator decision and a device-specific safety design. If
`validate:1.1` or confirmed commit is absent, report the reduced rollback
guarantee before applying a change.

Keep XML construction independent from ncclient. Validate namespaces, list
keys, `config true/false`, `choice/case`, `leafref`, `must`, `when`, and
deviations against the exact YANG revision supplied for the target release.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- HARD-BANNED: editing a NETCONF payload from a CLI label without checking the
  YANG path, namespace, revision, and device capability set.
- HARD-BANNED: disabling host-key verification, accepting unknown SSH keys, or
  embedding passwords, private keys, or tokens in code, fixtures, or logs.
- HARD-BANNED: assuming `candidate`, `validate`, `confirmed-commit`, rollback,
  XPath filtering, or notifications are supported because the session opened.
- Require a capability check before using any optional RPC or datastore.
- Lock the target datastore where supported; always unlock in cleanup, even
  after RPC errors, timeouts, or failed validation.
- Validate candidate configuration before commit and preserve the complete
  `rpc-error` details for operator diagnosis.
- Use confirmed commit with a bounded timeout for remote changes when the
  device supports it. Confirm only after postchecks pass; cancel or allow the
  timeout rollback on failure.
- Prefer `merge` for additive changes and make destructive `replace`, `delete`,
  and `remove` operations explicit in the request and review diff.
- Do not claim operational success from datastore state alone. Check the
  device's operational state, alarms, protocol neighbors, or service health.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Collect the device capability XML, NETCONF base version, YANG modules and
revision, datastore, operation type, desired intent, lock/commit support, and
postcheck definition. Reject a payload with unresolved namespaces, keys, or
read-only nodes.

### Phase 2 (Generation)

Build the payload or filter from the model, open a strictly verified ncclient
session, and execute a bounded transaction: capability check, lock, edit,
validate, commit or confirmed commit, postcheck, confirm/cancel, and unlock.
Keep payload generation and transaction control independently testable.

### Phase 3 (Self-Verification)

Run against XML fixtures or a NETCONF simulator before using a device. Test
unsupported capabilities, malformed namespaces, lock contention, validation
failure, RPC errors, timeout during commit, failed postcheck, and cleanup.
Verify that the resulting diff and audit record are sufficient to reconstruct
what was requested and what the device accepted.

## Production Code / Template Example

### Input / Requirement

Provide the device capability output, exact YANG revision, desired XML intent,
datastore, authentication and known_hosts references, confirmed-commit policy,
and operational postchecks. Do not infer support for optional NETCONF features.

### Output / Generated Code

Return a capability-gated transaction function that preserves RPC errors,
validates the candidate, uses confirmed commit when available, and always
releases the lock.

```python
from __future__ import annotations

from pathlib import Path

from ncclient import manager
from ncclient.operations.rpc import RPCError


REQUIRED_CAPABILITIES = {
    "urn:ietf:params:netconf:base:1.0",
    "urn:ietf:params:netconf:capability:candidate:1.0",
    "urn:ietf:params:netconf:capability:validate:1.1",
}


def apply_candidate(
    *, host: str, username: str, key_filename: str, known_hosts: str,
    config_xml: str, timeout: int = 30,
) -> None:
    with manager.connect(
        host=host,
        port=830,
        username=username,
        key_filename=key_filename,
        hostkey_verify=True,
        known_hosts=known_hosts,
        device_params={"name": "default"},
        timeout=timeout,
        allow_agent=False,
        look_for_keys=False,
    ) as session:
        capabilities = set(session.server_capabilities)
        missing = REQUIRED_CAPABILITIES - capabilities
        if missing:
            raise RuntimeError(f"device lacks required capabilities: {sorted(missing)}")

        with session.locked("candidate"):
            try:
                session.edit_config(
                    target="candidate",
                    config=config_xml,
                    default_operation="merge",
                    test_option="test-then-set",
                )
                session.validate(source="candidate")
                session.commit(confirmed=True, confirm_timeout=300)

                # Run device-specific operational postchecks here. Confirm only
                # after those checks pass; otherwise let the confirmed commit
                # expire or call cancel_commit() explicitly.
                session.commit()
            except RPCError:
                session.discard_changes()
                raise
```

## Validation, Linting & Testing Commands

- Validate XML namespaces and YANG structure with `xmllint`, `pyang`, or
  `yanglint` using the exact module revision and dependency path.
- Test capability negotiation, candidate locking, edit, validate, commit,
  confirmed commit, cancel, discard, unlock, and RPC error handling.
- Run fixture-backed tests for malformed XML, wrong namespace, missing key,
  read-only node, lock contention, timeout, and postcheck failure.
- Use a NETCONF simulator or lab device for datastore and confirmed-commit
  behavior; local XML validation cannot prove server semantics.
- Run `pytest` and `python3 scripts/validate_skills.py` from the repository root.

## References

- [RFC 6241: NETCONF Protocol](https://www.rfc-editor.org/rfc/rfc6241)
- [RFC 6242: NETCONF over SSH](https://www.rfc-editor.org/rfc/rfc6242)
- [RFC 6243: NETCONF Default Operations](https://www.rfc-editor.org/rfc/rfc6243)
- [ncclient documentation](https://ncclient.readthedocs.io/en/latest/)

## Offline Execution Contract

The skill can generate and validate payloads offline with local YANG modules,
capability XML, XML fixtures, and mocked ncclient responses. Without a target
or simulator, mark locking, server-side validation, commit behavior,
confirmed-commit rollback, notifications, and operational postchecks as
unverified.
