---
name: ncclient-restconf
description: "Build production Python model-driven clients with ncclient and httpx, using Pydantic or schema validation for XML/JSON payloads and safe NETCONF cleanup. Use this skill when an automation workflow must manage candidate datastores, locks, commits, and RESTCONF calls transactionally."
license: MIT
compatibility: Python 3.10+; ncclient; httpx; lxml; Pydantic optional; NETCONF/RESTCONF device capabilities
---

# ncclient/RESTCONF (Advanced)

Make the protocol session lifecycle explicit. A client that leaves a candidate datastore locked or changes unapplied after an exception is operationally incomplete even if its happy path works.

## Core Engineering Capabilities

- Use ncclient manager sessions for capabilities, filters, get-config, edits, locks, validation, commits, confirmed commits, and discard changes.
- Use httpx for RESTCONF with typed request/response models, timeouts, retries, pagination where supported, and media-type correctness.
- Build transaction wrappers that verify state and clean up locks/configuration.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Verify host keys and use secure credentials; never disable verification as a production default.
- Discover capabilities and reject unsupported datastores, models, or RPCs before mutation.
- Use `try/except/finally` to discard failed candidate changes and unlock every datastore acquired by the client. Make cleanup idempotent and observable.
- Use confirmed commit and explicit rollback timers for changes that can cut access. Do not assume a server supports every commit extension.
- Set connect, operation, and HTTP timeouts; classify RPC errors and preserve message-id/request-id context without logging secrets.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Identify the device endpoint, advertised capabilities, authentication and host-key policy, datastore or RESTCONF root, lock/commit behavior, timeout, and expected error payloads.

### Phase 2 (Implementation)

Generate a context-managed client with capability checks, namespace-aware filters, explicit transaction boundaries, bounded retries, and cleanup on every error path. Keep payload construction separate from transport.

### Phase 3 (Verification)

Run against local XML/JSON fixtures or a simulator, testing capability mismatch, malformed payload, lock contention, timeout, RPC error, and cleanup after failure. Never claim device success from client construction alone.

1. Connect, verify capabilities, and read the baseline.
2. Build and validate payload, lock the correct datastore, and edit candidate.
3. Validate/compare, commit or confirmed-commit, verify operational state.
4. On every failure, discard and unlock; report cleanup failures separately.

## Production Code / Template Example

### Input / Requirement

Provide endpoint and model metadata, operation type, payload or filter, datastore, commit strategy, timeout policy, and sanitized error fixtures.

### Output / Generated Code

Return the client module, payload/filter fixtures, mocked responses, exception mapping, and a runbook for verifying the same operation on a lab device.

```python
# client/netconf.py
from __future__ import annotations
from dataclasses import dataclass
from ncclient import manager
from ncclient.operations.rpc import RPCError
from lxml import etree

@dataclass
class NetconfResult:
    ok: bool
    response: str
    error: str | None = None

REQUIRED_CAPABILITIES = {
    "urn:ietf:params:netconf:base:1.0",
    "urn:ietf:params:netconf:capability:candidate:1.0",
    "urn:ietf:params:netconf:capability:validate:1.1",
}

def apply_candidate(
    *,
    host: str,
    username: str,
    key_filename: str,
    known_hosts: str,
    config_xml: str,
    timeout: int = 30,
) -> NetconfResult:
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
            return NetconfResult(ok=False, response="", error=f"device lacks required capabilities: {sorted(missing)}")

        session.lock("candidate")
        try:
            session.edit_config(target="candidate", config=config_xml, default_operation="merge", test_option="test-then-set")
            session.validate(source="candidate")
            session.commit(confirmed=True, confirm_timeout=300)
            return NetconfResult(ok=True, response="candidate committed with confirmed timer")
        except RPCError as e:
            session.discard_changes()
            return NetconfResult(ok=False, response="", error=f"RPC error: {e}")
        except Exception as e:
            session.discard_changes()
            return NetconfResult(ok=False, response="", error=f"unexpected error: {e}")
        finally:
            session.unlock("candidate")
```

```python
# client/restconf.py
import httpx
from pydantic import BaseModel
from typing import Optional

class RestconfResult(BaseModel):
    ok: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    status_code: int = 0

class RestconfClient:
    def __init__(self, base_url: str, token: str, timeout: float = 30.0):
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/yang-data+json"},
            timeout=httpx.Timeout(timeout, connect=10.0),
            verify=True,
        )

    def get(self, path: str) -> RestconfResult:
        try:
            resp = self.client.get(path)
            resp.raise_for_status()
            return RestconfResult(ok=True, data=resp.json(), status_code=resp.status_code)
        except httpx.HTTPStatusError as e:
            return RestconfResult(ok=False, error=f"HTTP {e.response.status_code}: {e.response.text}", status_code=e.response.status_code)
        except Exception as e:
            return RestconfResult(ok=False, error=str(e), status_code=0)
```

## Validation, Linting & Testing Commands

- Mock or lab-test capability mismatch, lock contention, RPC errors, timeout, confirmed-commit expiry, and cleanup failure.
- Assert the final state rather than trusting an `<ok/>` response alone.
- Run `python3 scripts/validate_skills.py`.

## References

- [ncclient GitHub](https://github.com/ncclient/ncclient)
- [ncclient documentation](https://ncclient.readthedocs.io/)
- [RFC 6241 NETCONF](https://www.rfc-editor.org/rfc/rfc6241.html)

## Offline Execution Contract

Use mocked ncclient/httpx sessions to test cleanup and transaction paths. Without a server or client libraries, preserve the transaction wrapper and classify live capability/commit validation as unexecuted.

## Architecture & Technical Design Patterns

Separate capability discovery from mutation. At session start, inspect `session.server_capabilities` and verify the required datastore, model namespace, `:candidate`, `:validate`, and confirmed-commit capability before calling those operations. Use `manager.connect(..., hostkey_verify=True, timeout=...)` and an explicit username/password or SSH-key reference.

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

For RESTCONF, use one shared `httpx.Client` with TLS verification, explicit timeouts, request IDs, typed response models, and bounded retry only for safe transient requests. Treat an HTTP success or NETCONF `<ok/>` as transport success; verify the resulting modeled state separately.