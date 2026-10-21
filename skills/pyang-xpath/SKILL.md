---
name: pyang-xpath
description: "[Tier: Basic] Inspect standard, OpenConfig, IETF, and vendor YANG models with pyang to produce schema trees, exact XPaths, and XML/JSON skeletons. Use this skill when designing NETCONF filters, RESTCONF paths, telemetry subscriptions, or model-driven automation from an existing YANG module."
license: MIT
compatibility: pyang; YANG module dependencies; Python optional for post-processing
---

# pyang XPath (Basic)

Use the model as the source of truth. Never infer namespaces, list keys,
config/state status, or XPath predicates from a device CLI name alone.

## Core Engineering Capabilities

- Resolve module imports and print `pyang -f tree` views.
- Distinguish `config true` writable nodes from `config false` operational
  state and identify list keys, namespaces, augments, and identities.
- Produce exact XPaths, NETCONF subtree filters, RESTCONF resource paths, and
  sample XML/JSON skeletons for selected nodes.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Pin or record the exact YANG module revision and dependency search path.
- Preserve namespace prefixes and list-key predicates exactly; a visually
  plausible XPath can still select the wrong node or no data.
- Do not send a read-only node in an edit payload or treat a choice/case as a
  concrete data node.
- Inspect augments and deviations before declaring a path portable across
  vendors. Vendor-native modules are not automatically OpenConfig-compatible.
- Separate schema inspection from device capability validation. A model may be
  installed but not advertised by a specific release.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Collect module, revision, and dependency files from the target release.
2. Run pyang tree and lint output, then inspect the selected node and ancestry.
3. Record namespace, config/state status, list keys, and exact path.
4. Generate skeleton payload/filter and validate it against the model or lab
   server before using it in automation.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```bash
pyang -p yang/ -f tree openconfig-interfaces.yang
pyang -p yang/ -f sample-xml-skeleton openconfig-interfaces.yang
```

```text
/interfaces/interface[name='Ethernet1']/config/description
```

## Validation, Linting & Testing Commands

- Run pyang with the complete dependency path and fail on errors.
- Verify `rw`/`ro` status, namespace, list keys, and revision against the
  target device capability set.
- Run `python3 scripts/validate_skills.py`.

## References

- [pyang](https://github.com/mbj4668/pyang)
- [RFC 7950 YANG 1.1](https://www.rfc-editor.org/rfc/rfc7950.html)

## Offline Execution Contract

Use locally supplied YANG modules and dependency paths. If pyang or a vendor model is unavailable, do not invent namespaces or XPaths; request/provide the exact model inputs and mark generated paths provisional.

## Architecture & Technical Design Patterns

For any selected node, record five facts: module name/revision, namespace and
prefix, absolute schema path, `config true/false`, and list keys. An XPath for
a keyed list must include predicates, for example:

```text
/oc-if:interfaces/oc-if:interface[oc-if:name='Ethernet1']/oc-if:config/oc-if:description
```

For NETCONF subtree filters, include the data namespace on the element and the
NETCONF base namespace only on the filter wrapper. For RESTCONF, use the
module-qualified resource path and URL-encode key values. Inspect `augment`,
`choice/case`, `identityref`, `leafref`, `when`, and deviations before
declaring a path portable. `config false` nodes belong in operational reads or
telemetry, not edit payloads.
