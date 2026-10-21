---
name: yang-model-dev
description: "[Tier: Expert] Author RFC 7950 YANG 1.1 modules for network automation services with containers, lists, leafrefs, typedefs, groupings, augments, must/when constraints, and feature gates. Use this skill when creating a new data model rather than merely consuming an existing vendor or OpenConfig model."
license: MIT
compatibility: pyang; YANG 1.1; RFC 7950/RFC 8407 knowledge; optional yanglint and model-driven test server
---

# YANG Model Development (Expert)

Design the model as a long-lived API. Names, namespaces, keys, defaults,
constraints, and status annotations become compatibility commitments once
clients and devices consume them.

## Core Engineering Capabilities

- Author modules with containers, keyed lists, leaf/leaf-list, typedefs,
  identities, groupings, augments, actions, notifications, and RPCs.
- Model IPs, prefixes, ASNs, VLANs, enums, ranges, patterns, references, and
  operational/configuration state accurately.
- Generate trees, sample XML/JSON, documentation, and schema-aware tests.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use YANG 1.1 explicitly, a stable namespace and revision history, SPDX/MIT
  licensing as appropriate, and clear `description`/`reference` statements.
- Use stable list keys and avoid keys that can change during lifecycle. Use
  `leafref` with correct `path` and `require-instance` semantics.
- Put constraints near the modeled data: `range`, `length`, `pattern`, `must`,
  and `when` must express operational invariants without impossible cycles.
- Distinguish `config true` and `config false`; do not make derived state
  writable just because it is convenient for a client.
- Avoid gratuitous breaking changes. Deprecate before removing and preserve
  namespace/module identity across revisions.
- Keep vendor augments isolated and document interoperability boundaries.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Write use cases, data ownership, lifecycle, cardinality, and compatibility
   requirements before syntax.
2. Define namespace, module/revision, typedefs, identities, containers, and
   list keys.
3. Add constraints and descriptions, then inspect tree and sample payloads.
4. Lint strictly with dependencies, validate XML/JSON instances, and test
   create/update/delete and invalid cases against a model-aware server.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```yang
module example-service {
  yang-version 1.1;
  namespace "https://example.net/yang/example-service";
  prefix ex;

  typedef vlan-id { type uint16 { range "1..4094"; } }
  container services {
    list service {
      key "name";
      leaf name { type string { length "1..64"; } }
      leaf vlan { type vlan-id; mandatory true; }
    }
  }
}
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Run `pyang --strict --lint -p yang/ module.yang` and resolve all errors and
  warnings intentionally.
- Run `yanglint` or an equivalent schema/instance validator when available.
- Generate tree and sample skeletons and review namespace, keys, `rw`/`ro`,
  constraints, and list cardinality.
- Run `sh skills/yang-model-dev/scripts/lint_yang.sh module.yang` and the root
  validator.

## References

- [RFC 7950 YANG 1.1](https://www.rfc-editor.org/rfc/rfc7950.html)
- [RFC 8407 YANG guidelines](https://www.rfc-editor.org/rfc/rfc8407.html)
- [pyang](https://github.com/mbj4668/pyang)

## Offline Execution Contract

YANG source, examples, and constraints must be complete in the skill output. If pyang/yanglint is unavailable, perform structural review and provide commands for later linting; never claim strict conformance.

## Architecture & Technical Design Patterns

Use this module order for a maintainable YANG 1.1 module: `yang-version`,
`namespace`, `prefix`, organization/contact, description, imports/includes,
revision history, typedefs/identities/groupings, then top-level data/RPC/
notification statements. Every public node needs a description and a clear
owner/lifecycle. Use hyphenated identifiers and stable list keys.

Model configuration under `config true` by default and derived device state
under `config false`. Use `leafref` for relationships, `must` for constraints
that can be evaluated in the same tree, and `when` for conditional presence.
Avoid a `must` expression that depends on an operational value unavailable
during configuration validation. Add `range`/`pattern` to IP, ASN, VLAN,
port, and name typedefs; use `union` only when the wire representation and
consumer behavior are unambiguous. For any schema change, classify it as
backward-compatible, deprecated, or breaking before changing the revision.
