---
name: network-rest-clients
description: "[Tier: Intermediate] Build typed Python REST clients with requests or httpx for Meraki, Arista eAPI, FortiOS, Palo Alto, and Cisco Catalyst Center APIs. Use this skill when network controller automation needs timeouts, token safety, pagination, rate-limit backoff, and structured errors."
license: MIT
compatibility: Python 3.10+; requests or httpx; tenacity optional; Pydantic optional; target controller API documentation and credentials
---

# Network REST Clients (Intermediate)

Build an API client around the target platform's documented contract, not a
collection of ad-hoc HTTP calls. The client should make safe behavior the
default and expose provider-specific differences at a clear boundary.

## Core Engineering Capabilities

- Implement typed request/response methods, authentication, pagination,
  filtering, retries, and resource CRUD for common network controllers.
- Support bearer tokens, API keys, or session authentication without logging
  credentials.
- Normalize HTTP errors into actionable exceptions while preserving request ID,
  status, endpoint, and redacted response context.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Set explicit connect and read timeouts on every request; never use an
  infinite default timeout.
- Retry only transient failures such as 429, 502, 503, and 504, with bounded
  exponential backoff and jitter. Respect `Retry-After` when present.
- Never retry non-idempotent POST/PATCH operations without an idempotency key
  or a documented provider guarantee.
- Implement pagination until the provider indicates completion; guard against
  repeated cursors and unreasonable page counts.
- Read tokens from environment or secret managers, use HTTPS verification,
  and redact authorization headers and secret fields in logs.
- Validate response schemas and preserve unknown fields when forward
  compatibility matters. Do not silently treat an error envelope as data.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Record the API base URL and version, authentication method, resource identity, pagination shape, rate-limit headers, retryable status codes, timeout, and idempotency key policy.

### Phase 2 (Implementation)

Implement a typed client with session reuse, bounded retries, backoff, pagination, request correlation, and response validation. Keep authentication external and never retry a non-idempotent mutation without an explicit contract.

### Phase 3 (Verification)

Replay success, pagination, 429, 5xx, malformed response, timeout, auth failure, and duplicate-request fixtures. Verify retry counts, backoff bounds, and that sensitive headers never appear in logs.

1. Read the target API's versioned documentation and identify auth, limits,
   pagination, mutation semantics, and idempotency behavior.
2. Build a transport layer for timeout, headers, retry, and error handling.
3. Add resource methods with typed models and explicit pagination.
4. Test against mocked responses for success, empty pages, rate limits,
   expired credentials, malformed data, and server errors.
5. Run read-only discovery first; gate mutations behind dry-run, diff, and
   explicit authorization.

## Production Code / Template Example

### Input / Requirement

Provide API documentation or fixtures, resource schema, authentication contract, retry policy, pagination examples, and the operations that must be idempotent.

### Output / Generated Code

Return the client module, models, fixture suite, retry behavior, and an example showing safe list, create, update, and delete handling.


```python
import os
import httpx

def list_devices(base_url: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {os.environ['CONTROLLER_TOKEN']}"}
    devices, url = [], f"{base_url}/api/devices"
    with httpx.Client(headers=headers, timeout=httpx.Timeout(10.0, read=30.0)) as client:
        while url:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
            devices.extend(payload.get("items", []))
            next_url = payload.get("next")
            if next_url == url:
                raise RuntimeError("controller returned a repeated pagination cursor")
            url = next_url
    return devices
```

## Validation, Linting & Testing Commands

- Mock 429, `Retry-After`, malformed JSON, pagination loops, and 401/403 cases.
- Verify no request lacks a timeout and no logs contain tokens or secret fields.
- Test idempotent create/update behavior against a disposable controller or
  mocked contract.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [HTTPX documentation](https://www.python-httpx.org/)
- [Requests documentation](https://requests.readthedocs.io/)
- [Tenacity documentation](https://tenacity.readthedocs.io/)

## Offline Execution Contract

Use local mocked HTTP responses for pagination, retries, and error handling. Without the target API, generate typed client code and fixtures from supplied schemas only; never guess endpoint or response fields.

## Architecture & Technical Design Patterns

Separate `Transport`, `Auth`, `Pagination`, `Models`, and `Resources`. Every
request must set a connect/read timeout and include a correlation/request ID
when the provider supports it. Map responses as follows: `2xx` success,
`401/403` authentication/authorization failure with no retry, `404` missing
resource, `409` conflict requiring reconciliation, `429` backoff using
`Retry-After`, and `5xx` bounded exponential retry. Retry `GET`, `HEAD`, and
documented idempotent mutations only.

Pagination must track the previous cursor/URL and a maximum page count. For
cursor APIs, follow the provider's `next` field; for offset APIs, increment by
the returned page size and stop on an empty page. Validate each response into
a typed model before adding it to the result. Log method, path, status,
duration, and request ID, but redact authorization headers, tokens, and secret
response fields.
