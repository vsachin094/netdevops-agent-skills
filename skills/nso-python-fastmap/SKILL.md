---
name: nso-python-fastmap
description: "[Tier: Advanced] Develop Cisco NSO Python-backed service packages using ServiceCallbacks, `ncs.maapi`, `ncs.maagic`, and `ncs.template.Template`. Use this skill when service mapping requires dynamic allocation, validation, or logic beyond XML templates while preserving FASTMAP transaction semantics."
license: MIT
compatibility: Cisco NSO Python API; YANG; compatible NED packages; NSO development environment
---

# NSO Python FASTMAP (Advanced)

Write service code inside NSO's transaction model. FASTMAP tracks changes made
through the supplied service transaction; out-of-band writes defeat rollback,
diffs, and reconciliation.

## Core Engineering Capabilities

- Scaffold `python-and-template` service packages and implement `cb_create`.
- Read service data with maagic, allocate resources from an approved source,
  add template variables, and validate references before applying templates.
- Produce service package tests, dry-runs, redeploy behavior, and rollback
  diagnostics.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Keep `cb_create` transaction-pure. Do not open an unrelated MAAPI
  transaction, write directly to devices, or call an external API that changes
  state inside the callback.
- Make resource allocation deterministic and idempotent. Reserve/claim an IP,
  VLAN, or ID through a transaction-aware source and release it on failure.
- Validate device leafrefs and service input before calling `Template.apply`.
- Use `ncs.template.Template(service)` with the callback's transaction context;
  never construct a detached write path for convenience.
- Keep callbacks bounded and observable; move long-running external work to a
  supported asynchronous/Nano Service design.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Identify the service YANG model, keypath, input leaves, device or service dependencies, and the exact create/update/delete behavior. Separate transaction-time mapping from operational side effects.

### Phase 2 (Implementation)

Implement FASTMAP callbacks that read transaction data, create deterministic service components, and map dependencies without opening out-of-band MAAPI transactions. Keep validation and side effects in the correct NSO phase.

### Phase 3 (Verification)

Compile the package and exercise create, update, delete, invalid input, duplicate key, and dependency failure cases. Inspect transaction diffs and confirm rollback leaves the CDB consistent.

1. Define service YANG and allocation ownership.
2. Scaffold package and implement callback with validation and template apply.
3. Run compile, dry-run, service create/update/delete, and failure injection.
4. Inspect NSO transaction diff and verify no external side effects escape the
   transaction.

## Production Code / Template Example

### Input / Requirement

Provide the service model, Python package skeleton, keypaths, component mapping, validation rules, and expected transaction outcomes.

### Output / Generated Code

Return the package code, service model changes, mapping explanation, test fixtures, compile commands, and known platform prerequisites.


```python
class ServiceCallbacks(ncs.application.Service):
    @ncs.service.create
    def cb_create(self, tctx, root, service, proplist):
        vars = ncs.template.Variables()
        vars.add("DEVICE", service.device)
        vars.add("VLAN_ID", service.vlan_id)
        template = ncs.template.Template(service)
        template.apply("service-template", vars)
```

The callback must use the actual generated service model and include explicit
validation/error handling; this example shows the transaction boundary only.

## Validation, Linting & Testing Commands

- Test first create, update, delete, duplicate allocation, failed template,
  and `no service` rollback.
- Run `commit dry-run outformat native`, package compile, and NSO service tests.
- Run `python3 scripts/validate_skills.py`.

## References

- [NSO Python template API](https://nso-docs.cisco.com/guides/developer-reference/pyapi/ncs.template)
- [NSO FASTMAP service development](https://nso-docs.cisco.com/guides/nso-6.1/development/introduction-to-automation/develop-a-simple-service)

## Offline Execution Contract

Keep callback logic testable with mocked maagic/template objects. Without NSO, validate transaction boundaries and generated package structure only; do not claim FASTMAP rollback or NED rendering was executed.

## Architecture & Technical Design Patterns

The callback receives NSO's transaction context and service node; use the
service node to read input and `ncs.template.Template(service)` to apply
configuration. Do not call `ncs.maapi.single_write_trans()` or open a second
transaction inside `cb_create`. That breaks FASTMAP's change tracking and
`no service` rollback. Keep external allocation read-only or move reservation
to a supported transaction-aware integration.

Callback flow: validate service leafrefs and prerequisites, derive deterministic
template variables, apply the template, and return. Raise a precise
`ncs.dp.NcsError`/Python exception with service path and cause on failure. Do
not perform long-running HTTP calls, direct device SSH, sleeps, or background
threads in a synchronous callback. Test first create, update, delete, duplicate
resource, failed template, and rollback under the actual generated YANG model.
