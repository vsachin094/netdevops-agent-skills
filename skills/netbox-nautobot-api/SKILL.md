---
name: netbox-nautobot-api
description: "[Tier: Intermediate] Build pynetbox or pynautobot automation, GraphQL queries, webhooks, and synchronization jobs for NetBox/Nautobot as network source of truth. Use this skill when IPAM/DCIM/inventory objects must be read, reconciled, or created idempotently."
license: MIT
compatibility: Python 3.10+; pynetbox or pynautobot; requests/httpx; GraphQL; NetBox/Nautobot API token
---

# NetBox/Nautobot API (Intermediate)

Treat the source of truth as an API with schema, permissions, pagination, and
concurrency behavior. Idempotency depends on stable natural keys and explicit
ownership, not on catching duplicate errors after the fact.

## Core Engineering Capabilities

- Read and reconcile sites, devices, interfaces, prefixes, IPs, VLANs, VRFs,
  circuits, and custom fields.
- Use GraphQL for nested bulk reads and REST/pynetbox/pynautobot for controlled
  writes, webhooks, and synchronization.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Read tokens from environment/secret manager and verify TLS.
- Use slug/name/external ID lookups before create; never create duplicates
  because a list endpoint was paginated incorrectly.
- Prefer GraphQL for nested bulk reads to avoid REST N+1 patterns; use REST
  endpoints for mutations supported by the target version.
- Handle pagination, rate limits, permissions, schema/version differences,
  and webhook retries explicitly.
- Scope writes by tenant/site/VRF ownership and use dry-run diffs where the
  API or workflow supports them.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Identify the object type, unique key, tenancy and site scope, custom fields, relationship requirements, API version, pagination behavior, and dry-run expectation. Use recorded responses when the source of truth is unavailable.

### Phase 2 (Implementation)

Generate idempotent API operations that reconcile by stable natural keys, validate foreign references, paginate safely, and distinguish create, update, no-op, and delete. Keep tokens outside code and logs.

### Phase 3 (Verification)

Replay create, update, unchanged, missing-parent, pagination, rate-limit, and permission-denied fixtures. Confirm the second reconciliation is a no-op and that deletion requires an explicit policy.

1. Discover target version/schema and define natural keys.
2. Read and normalize existing objects, calculate diff, and validate ownership.
3. Apply idempotent changes in dependency order, then re-read and verify.

## Production Code / Template Example

### Input / Requirement

Provide object definitions, unique keys, desired records, API version, relationship graph, authentication method, and the expected dry-run or diff format.

### Output / Generated Code

Return the client or module, request/response fixtures, reconciliation report, and tests for create, update, no-op, reference failure, and pagination.


```python
import os, pynetbox
nb = pynetbox.api(os.environ["NETBOX_URL"], token=os.environ["NETBOX_TOKEN"])
device = nb.dcim.devices.get(name="edge-1")
if device is None:
    device = nb.dcim.devices.create(name="edge-1", site=1, device_type=2, role=1, status="active")
```

## Validation, Linting & Testing Commands

- Test pagination, duplicate natural keys, permission errors, stale webhook,
  rate limit, and partial write failure.
- Re-read objects after mutation and assert fields, parent relationships, and
  VRF scope.
- Run `python3 scripts/validate_skills.py`.

## References

- [NetBox REST API](https://github.com/netbox-community/netbox/blob/main/docs/integrations/rest-api.md)
- [NetBox GraphQL](https://netbox.readthedocs.io/en/stable/configuration/graphql-api/)
- [pynetbox](https://netbox-community.github.io/pynetbox/api/)

## Offline Execution Contract

Use saved REST/GraphQL fixtures and local schema snapshots for reads, diffs, and idempotency tests. Without NetBox/Nautobot, do not invent object IDs or claim a write succeeded.

## Architecture & Technical Design Patterns

Use natural keys appropriate to each object: device name within a site/tenant,
interface name within a device, prefix plus VRF, and IP plus VRF. Resolve
foreign objects before creating children and keep a local cache for a single
reconciliation run. For bulk reads, request only required fields through
GraphQL or paginated REST; for writes, read the current object, calculate a
field-level diff, and update only owned fields.

Handle `401/403` as credential/permission failure, `404` as missing object,
`409` as an ownership/concurrency conflict, and `429/5xx` with bounded retry.
Use webhook event IDs for deduplication and replay protection. After a write,
re-read the object and verify parent, status, VRF, role, and custom fields.
Never use a broad delete to reconcile an incomplete API result.
