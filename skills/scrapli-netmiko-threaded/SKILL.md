---
name: scrapli-netmiko-threaded
description: "[Tier: Intermediate] Scale SSH collection and controlled changes across network devices with ThreadPoolExecutor using Scrapli or Netmiko. Use this skill when a bounded fleet workflow needs per-device failures, concurrency limits, and JSON/CSV execution summaries."
license: MIT
compatibility: Python 3.10+; concurrent.futures; Scrapli or Netmiko; optional Pydantic and Rich
---

# Scrapli/Netmiko Threaded (Intermediate)

Treat each worker as an isolated job with a bounded lifetime. Fleet automation
must return a complete result set even when devices are unreachable, slow, or
partially successful.

## Core Engineering Capabilities

- Execute read or explicitly authorized write jobs across a device inventory.
- Limit worker count, connection rate, command timeouts, and retry budgets.
- Handle authentication, timeout, transport, parsing, and unexpected errors
  per device without killing the batch.
- Emit stable JSON/CSV results with status, duration, exception type, and
  redacted diagnostics.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use `ThreadPoolExecutor` with a deliberate `max_workers`; never equate more
  threads with more throughput on a control plane or TACACS service.
- Catch `NetmikoTimeoutException`, `NetmikoAuthenticationException`,
  `ScrapliException`, and general exceptions inside the worker, mapping them
  to a result object.
- Do not share mutable connection objects across threads. Create and close one
  session per job.
- Use idempotent operations, dry-run mode, and a fleet-level approval gate for
  writes. A failed worker must not trigger an implicit retry of a change.
- Preserve input order or sort results by stable device ID before serialization.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Validate inventory uniqueness and required connection fields.
2. Partition read versus write jobs and establish a bounded concurrency policy.
3. Submit one isolated worker per device and collect every future with
   `return_exceptions`-equivalent handling.
4. Serialize results, return a non-zero process status for policy-defined
   failures, and include a retry list without automatically applying changes.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_one(device):
    try:
        with make_connection(device) as conn:
            return {"device": device["name"], "status": "ok",
                    "output": conn.send_command("show version")}
    except Exception as exc:
        return {"device": device["name"], "status": "error",
                "error_type": type(exc).__name__}

with ThreadPoolExecutor(max_workers=20) as pool:
    results = [future.result() for future in as_completed(pool.submit(run_one, d) for d in inventory)]
results.sort(key=lambda item: item["device"])
```

## Validation, Linting & Testing Commands

- Test unreachable, authentication failure, timeout, parser failure, and
  successful device paths independently.
- Load-test the chosen worker count in a lab and measure AAA/control-plane
  impact before increasing it.
- Assert every input device has exactly one result.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Python `concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html)
- [Scrapli documentation](https://carlmontargett.github.io/scrapli/)
- [Netmiko documentation](https://ktbyers.github.io/netmiko/)

## Offline Execution Contract

Use local mocked workers to test concurrency, result aggregation, and failure isolation. Without Scrapli/Netmiko or devices, do not fabricate transport success; return a dependency-blocked result with the same schema.

## Architecture & Technical Design Patterns

Define one result schema for every worker:

```python
{"device": "edge-1", "status": "ok|timeout|auth_error|transport_error|parse_error", "duration_s": 1.2, "attempts": 1, "data": {}, "error": None}
```

Validate inventory before submitting futures, deduplicate by stable device ID,
and use `ThreadPoolExecutor(max_workers=N)` with `as_completed()`. The worker
must create its own connection, set connect/read timeouts, and close it in a
`finally`/context-manager path. Retry read-only collection only for bounded
transient failures; never automatically retry a write. Sort results by device
ID after collection, calculate `success`, `failed`, and `skipped` counts, and
return exit code 2 when the policy-defined failure threshold is exceeded.
