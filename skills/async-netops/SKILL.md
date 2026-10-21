---
name: async-netops
description: "[Tier: Expert] Build high-concurrency asynchronous network automation with asyncio, AsyncScrapli, asyncssh, and httpx.AsyncClient for large fleets. Use this skill when thousands of independent network or API operations require bounded concurrency, cancellation, backpressure, and complete per-device results."
license: MIT
compatibility: Python 3.10+; asyncio; AsyncScrapli or asyncssh; httpx; Pydantic optional; target devices or APIs
---

# Async NetOps (Expert)

Concurrency is a capacity-management problem, not a loop syntax problem.
Design explicit limits for connections, commands, API requests, memory, and
retries, then make cancellation and partial failure observable.

## Core Engineering Capabilities

- Execute asynchronous SSH and HTTP operations across large inventories.
- Use semaphores, bounded queues, task groups, deadlines, and cancellation
  handling to protect devices, AAA, controllers, and the event loop.
- Aggregate results with typed status, latency, retry count, and exception
  metadata while preserving input identity.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use `asyncio.Semaphore(N)` or a bounded worker queue for every scarce
  external resource. Do not create one task per device without a limit.
- Use `asyncio.gather(..., return_exceptions=True)` or structured concurrency
  so one failure does not erase the fleet result.
- Set per-operation and overall deadlines; cancel and close sessions in
  `finally` paths. Do not block the event loop with synchronous libraries.
- Retry only safe, transient operations with exponential backoff and jitter.
  Never automatically retry a non-idempotent network change.
- Bound result and raw-output memory; stream or summarize large output.
- Handle SIGINT/SIGTERM and propagate cancellation without leaving sessions or
  candidate configurations open.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Quantify fleet size, per-device timeout, concurrency budget, retry policy, rate limits, cancellation behavior, and the operation's idempotency. Separate connection errors from device command failures before writing the worker pool.

### Phase 2 (Generation)

Implement bounded concurrency with semaphores or a worker queue, per-task timeouts, structured results, and cancellation-safe cleanup. Preserve input order or expose an explicit correlation key so operators can reconcile outcomes.

### Phase 3 (Self-Verification)

Run against local fakes that simulate slow devices, timeouts, rate-limit responses, cancellation, malformed payloads, and partial success. Measure concurrency and verify no task or connection is leaked.

1. Classify operations as read-only, idempotent write, or non-repeatable.
2. Choose concurrency and rate limits from platform capacity and lab tests.
3. Implement one resource-safe coroutine and test it independently.
4. Schedule bounded tasks, gather complete results, and emit retry candidates
   separately from successful or failed operations.

## Production Code / Template Example

### Input / Requirement

Provide the device inventory, operation contract, fleet size, timeout and rate limits, retryable errors, and the required result schema.

### Output / Generated Code

Return the async worker implementation, configuration knobs, structured result example, fixture-based tests, and an explanation of retry and cancellation semantics.


```python
import asyncio

async def collect(device: dict, limit: asyncio.Semaphore) -> dict:
    async with limit:
        try:
            async with make_async_connection(device) as conn:
                output = await asyncio.wait_for(conn.send_command("show version"), 30)
            return {"device": device["name"], "status": "ok", "output": output}
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return {"device": device["name"], "status": "error", "error": type(exc).__name__}

async def main(inventory: list[dict]) -> list[dict]:
    limit = asyncio.Semaphore(100)
    return await asyncio.gather(*(collect(d, limit) for d in inventory), return_exceptions=False)
```

## Validation, Linting & Testing Commands

- Test timeouts, cancellation, connection leaks, semaphore limits, transient
  retries, and partial fleet failure.
- Measure event-loop lag, AAA load, open sessions, and memory at target scale.
- Run a lab soak test before increasing concurrency.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [AsyncSSH documentation](https://asyncssh.readthedocs.io/)
- [AsyncScrapli documentation](https://carlmontargett.github.io/scrapli/user_guide/advanced_usage/asyncssh/)

## Offline Execution Contract

Test coroutines with local fake transports, timeouts, cancellation, and bounded concurrency. Without async transport libraries or devices, verify scheduling and result semantics only; never report network success.

## Architecture & Technical Design Patterns

Use a bounded producer/consumer model for large inventories. A semaphore
limits simultaneous operations; a queue limits memory; a deadline limits one
operation; and a task-group/gather boundary collects every result. Always
re-raise `asyncio.CancelledError` so shutdown works. Close `AsyncClient`, SSH,
and device sessions in `async with` or `finally` blocks.

Classify operations before scheduling: reads may have bounded transient retry;
idempotent writes may retry only with an idempotency key or verified state;
non-repeatable writes must not retry automatically. Use jittered backoff,
per-device locks when two tasks can touch one device, and a global rate limit
for AAA/controller requests. Report `cancelled`, `timeout`, `auth_error`,
`transport_error`, and `ok` distinctly rather than flattening all exceptions.
