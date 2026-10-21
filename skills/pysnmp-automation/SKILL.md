---
name: pysnmp-automation
description: "[Tier: Advanced] Build Python SNMP automation with PySNMP for SNMPv1/v2c/v3 GET, SET, GETBULK, walks, traps, informs, MIB resolution, asyncio concurrency, and typed result handling. Use this skill when a Python program must poll or change SNMP-managed infrastructure directly rather than configure an exporter or dashboard pipeline."
license: MIT
compatibility: Python 3.10+; PySNMP 7.1+; pysmi optional for local MIB compilation; pytest; SNMPv1/v2c/v3 agent or simulator
---

# PySNMP Automation (Advanced)

Use PySNMP as a protocol client with an explicit data and security contract.
SNMP is not a reliable configuration transaction protocol: a response can
confirm a PDU was accepted without proving that the device reached the desired
operational state. Prefer SNMPv3 authPriv for production and keep SET
operations narrowly scoped, reviewed, and separately enabled.

## Core Engineering Capabilities

- Build Python managers for GET, GETNEXT, GETBULK, bounded walks, and carefully
  approved SET operations using the PySNMP high-level asyncio API.
- Support SNMPv1/v2c for compatibility fixtures and SNMPv3 USM with explicit
  authentication and privacy settings for production polling.
- Resolve standard and vendor MIB objects from local MIB paths, while keeping
  numeric OID operation available when a MIB package is not present.
- Handle contexts, IPv4/IPv6 transports, timeouts, retries, `noSuchObject`,
  `noSuchInstance`, `endOfMibView`, PDU errors, and engine-level errors.
- Implement bounded concurrent polling with per-target limits, structured
  results, cancellation, and correlation to the source inventory.
- Send and receive traps or informs with explicit bind addresses, non-privileged
  test ports, notification validation, and clean dispatcher shutdown.
- Convert ASN.1 values into typed application records without losing the raw
  OID, SNMP type, source address, timestamp, or error context.

## Architecture & Technical Design Patterns

Separate inventory, credentials, OID definitions, transport, protocol result
handling, and application normalization:

```text
inventory + credential reference + OID/MIB contract
                    │
                    ▼
             PySNMP engine/dispatcher
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
      GET         WALK/GETBULK   SET
       │            │            │
       └────────────┴────────────┘
                    ▼
          typed result + audit record
```

Use the v3arch asyncio API when SNMPv3 or a unified high-level interface is
required. Use the v1arch asyncio API when a high-volume v1/v2c poller benefits
from its lighter dispatcher. Do not mix API architectures casually; the engine
and dispatcher types, authentication objects, and lifecycle differ.

Keep one dispatcher or engine per event-loop lifecycle and do not share a
mutable engine across unrelated threads. Bound concurrency with a semaphore,
reuse transport state where the API supports it, and close the dispatcher in a
finally block. A walk must have a root OID, a maximum row count, a timeout, and
an end-of-subtree condition; never loop until an agent stops responding.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- HARD-BANNED: hardcoded community strings, SNMPv3 usernames, authentication
  keys, privacy keys, or engine IDs in source, fixtures, logs, or prompts.
- HARD-BANNED: using the default `public` community against production or
  treating SNMPv1/v2c as equivalent to authenticated and encrypted SNMPv3.
- HARD-BANNED: enabling SET operations without an explicit allow-list of OIDs,
  ASN.1 types, expected old values, intended new values, and postchecks.
- Require a per-target timeout, bounded retries, a maximum walk size, and a
  clear policy for unreachable agents and partial results.
- Distinguish transport errors, SNMP engine errors, PDU error status, and valid
  values such as `noSuchInstance` or `endOfMibView`; do not convert them all to
  null or zero.
- Verify the OID remains within the requested subtree during GETNEXT or
  GETBULK walks. Stop on non-increasing OIDs, end-of-view, or the row limit.
- Use local MIB files and pinned revisions. Never fetch MIBs dynamically during
  a restricted or production run unless that behavior is explicitly approved.
- Redact credentials and sensitive varbind values from logs. Record target,
  OID, operation, status, latency, and correlation ID for auditability.
- Treat SET as a change operation: use a dry-run representation, record the
  previous value where safe, verify the response, and run a device-specific
  operational postcheck.
- Bind trap receivers to a non-privileged test port unless the deployment has
  deliberately granted the capability required for UDP/162.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Collect the SNMP version, target addresses, context names, credential
references, OIDs or MIB objects, polling interval, timeout/retry budget,
maximum walk size, and output schema. Confirm that every OID is readable or
explicitly approved for SET and that the target supports the selected security
model.

### Phase 2 (Generation)

Create a Python asyncio manager with the correct PySNMP architecture, typed
authentication, transport targets, bounded concurrency, and explicit result
handling. Keep OID definitions and credentials outside the polling function;
make notification and SET paths opt-in rather than incidental.

### Phase 3 (Self-Verification)

Run the manager against a local SNMP simulator or fixture-backed fake. Test
valid values, timeouts, retries, invalid credentials, unsupported OIDs,
`endOfMibView`, non-increasing walk output, SET rejection, cancellation, and
dispatcher cleanup. Verify both numeric OID and MIB-resolved output where MIBs
are available.

## Production Code / Template Example

### Input / Requirement

Provide the target address, SNMP version, external credential reference, MIB or
numeric OID, context, timeout/retry policy, and typed output contract. For a
SET, provide the approved OID/value allow-list and the operational postcheck.

### Output / Generated Code

Return a Python asyncio poller that uses SNMPv3 authPriv, applies bounded
timeouts, preserves error classes, and closes the PySNMP engine cleanly.

```python
from __future__ import annotations

import asyncio
import os

from pysnmp.hlapi.v3arch.asyncio import (
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    get_cmd,
    usmAesCfb128Protocol,
    usmHMACSHAAuthProtocol,
)


async def get_sys_name(host: str) -> str:
    engine = SnmpEngine()
    try:
        auth = UsmUserData(
            os.environ["SNMPV3_USER"],
            authKey=os.environ["SNMPV3_AUTH_KEY"],
            privKey=os.environ["SNMPV3_PRIV_KEY"],
            authProtocol=usmHMACSHAAuthProtocol,
            privProtocol=usmAesCfb128Protocol,
        )
        target = await UdpTransportTarget.create(
            (host, 161), timeout=2, retries=1
        )
        error_indication, error_status, error_index, var_binds = await get_cmd(
            engine,
            auth,
            target,
            ContextData(),
            ObjectType(ObjectIdentity("SNMPv2-MIB", "sysName", 0)),
        )
        if error_indication:
            raise RuntimeError(f"SNMP engine error from {host}: {error_indication}")
        if error_status:
            failed_oid = var_binds[int(error_index) - 1][0] if error_index else "?"
            raise RuntimeError(
                f"SNMP PDU error from {host}: {error_status} at {failed_oid}"
            )
        if len(var_binds) != 1:
            raise RuntimeError(f"unexpected varbind count from {host}")
        return var_binds[0][1].prettyPrint()
    finally:
        engine.close_dispatcher()


async def main() -> None:
    hosts = ["192.0.2.10", "192.0.2.11"]
    results = await asyncio.gather(
        *(get_sys_name(host) for host in hosts), return_exceptions=True
    )
    for host, result in zip(hosts, results, strict=True):
        if isinstance(result, Exception):
            print({"host": host, "ok": False, "error": str(result)})
        else:
            print({"host": host, "ok": True, "sysName": result})


if __name__ == "__main__":
    asyncio.run(main())
```

## Validation, Linting & Testing Commands

- Install the pinned Python dependency in a virtual environment and run
  `python -m compileall` plus `ruff check` or the configured linter.
- Test SNMPv1/v2c compatibility only with isolated lab credentials and test
  agents; test production paths with SNMPv3 authPriv.
- Exercise GET, GETBULK, bounded walk, error status, timeout, retry, invalid
  credentials, unsupported OID, IPv6 target, and context-name cases.
- Run SET only against a disposable agent and assert old value, response, and
  postcheck; include a rejected SET fixture.
- Test trap/inform send and receive using a non-privileged local port and verify
  varbind type, source, notification OID, and duplicate handling.
- Run `pytest` with credentials and real network addresses excluded from tests.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [PySNMP 7.1 quick start](https://docs.lextudio.com/pysnmp/v7.1/quick-start)
- [PySNMP v3arch asyncio GET API](https://docs.lextudio.com/pysnmp/v7.1/docs/hlapi/v3arch/asyncio/manager/cmdgen/getcmd)
- [PySNMP v1arch asyncio GET API](https://docs.lextudio.com/pysnmp/v7.1/docs/hlapi/v1arch/asyncio/manager/cmdgen/getcmd)
- [PySNMP source repository](https://github.com/pysnmp/pysnmp)
- [RFC 3411: SNMP architecture](https://www.rfc-editor.org/rfc/rfc3411)
- [RFC 3414: USM for SNMPv3](https://www.rfc-editor.org/rfc/rfc3414)

## Offline Execution Contract

The skill can generate and test Python SNMP code offline with PySNMP, local
MIBs, synthetic varbind fixtures, and an SNMP simulator or disposable agent.
Without a target, mark UDP reachability, device MIB support, authentication,
SET behavior, trap delivery, and operational postchecks as unverified.
