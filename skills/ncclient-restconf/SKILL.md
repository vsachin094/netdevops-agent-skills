---
name: ncclient-restconf
description: "[Tier: Advanced] Build production Python model-driven clients with ncclient and httpx, using Pydantic or schema validation for XML/JSON payloads and safe NETCONF cleanup. Use this skill when an automation workflow must manage candidate datastores, locks, commits, and RESTCONF calls transactionally."
license: MIT
compatibility: Python 3.10+; ncclient; httpx; lxml; Pydantic optional; NETCONF/RESTCONF device capabilities
---

# ncclient/RESTCONF (Advanced)

Make the protocol session lifecycle explicit. A client that leaves a candidate
datastore locked or changes unapplied after an exception is operationally
incomplete even if its happy path works.

## Core Engineering Capabilities

- Use ncclient manager sessions for capabilities, filters, get-config, edits,
  locks, validation, commits, confirmed commits, and discard changes.
- Use httpx for RESTCONF with typed request/response models, timeouts, retries,
  pagination where supported, and media-type correctness.
- Build transaction wrappers that verify state and clean up locks/configuration.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Verify host keys and use secure credentials; never disable verification as a
  production default.
- Discover capabilities and reject unsupported datastores, models, or RPCs
  before mutation.
- Use `try/except/finally` to discard failed candidate changes and unlock every
  datastore acquired by the client. Make cleanup idempotent and observable.
- Use confirmed commit and explicit rollback timers for changes that can cut
  access. Do not assume a server supports every commit extension.
- Set connect, operation, and HTTP timeouts; classify RPC errors and preserve
  message-id/request-id context without logging secrets.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Connect, verify capabilities, and read the baseline.
2. Build and validate payload, lock the correct datastore, and edit candidate.
3. Validate/compare, commit or confirmed-commit, verify operational state.
4. On every failure, discard and unlock; report cleanup failures separately.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
from ncclient import manager

with manager.connect(host=host, port=830, username=user, password=password,
                     hostkey_verify=True, timeout=20) as session:
    session.lock(target="candidate")
    try:
        session.edit_config(target="candidate", config=payload)
        session.validate(source="candidate")
        session.commit(confirmed=True, confirm_timeout=60)
    except Exception:
        session.discard_changes()
        raise
    finally:
        session.unlock(target="candidate")
```

## Validation, Linting & Testing Commands

- Mock or lab-test capability mismatch, lock contention, RPC errors, timeout,
  confirmed-commit expiry, and cleanup failure.
- Assert the final state rather than trusting an `<ok/>` response alone.
- Run `python3 scripts/validate_skills.py`.

## References

- [ncclient GitHub](https://github.com/ncclient/ncclient)
- [ncclient documentation](https://ncclient.readthedocs.io/)
- [RFC 6241 NETCONF](https://www.rfc-editor.org/rfc/rfc6241.html)

## Offline Execution Contract

Use mocked ncclient/httpx sessions to test cleanup and transaction paths. Without a server or client libraries, preserve the transaction wrapper and classify live capability/commit validation as unexecuted.

## Architecture & Technical Design Patterns

Separate capability discovery from mutation. At session start, inspect
`session.server_capabilities` and verify the required datastore, model
namespace, `:candidate`, `:validate`, and confirmed-commit capability before
calling those operations. Use `manager.connect(..., hostkey_verify=True,
timeout=...)` and an explicit username/password or SSH-key reference.

Wrap candidate operations in a cleanup boundary:

```python
session.lock("candidate")
try:
    session.edit_config(target="candidate", config=payload)
    session.validate(source="candidate")
    session.commit(confirmed=True, confirm_timeout=120)
except Exception:
    session.discard_changes()
    raise
finally:
    session.unlock("candidate")
```

For RESTCONF, use one shared `httpx.Client` with TLS verification, explicit
timeouts, request IDs, typed response models, and bounded retry only for safe
transient requests. Treat an HTTP success or NETCONF `<ok/>` as transport
success; verify the resulting modeled state separately.
