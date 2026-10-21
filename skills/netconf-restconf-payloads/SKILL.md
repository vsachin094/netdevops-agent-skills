---
name: netconf-restconf-payloads
description: "[Tier: Intermediate] Construct namespace-correct NETCONF XML and RESTCONF JSON/XML payloads for OpenConfig and vendor YANG models, including filters, edits, locks, validation, and confirmed commits. Use this skill when model-driven configuration needs exact protocol envelopes and rollback semantics."
license: MIT
compatibility: Python 3.10+; lxml or xml.etree; requests/httpx optional; pyang; target YANG models and device capabilities
---

# NETCONF/RESTCONF Payloads (Intermediate)

Payload correctness depends on both protocol and model. Keep the YANG data
namespace, NETCONF base namespace, RESTCONF media type, datastore, and edit
operation explicit.

## Core Engineering Capabilities

- Build NETCONF `<get>`, `<get-config>`, `<edit-config>`, `<lock>`, `<unlock>`,
  `<validate>`, `<commit>`, and confirmed-commit workflows.
- Build RESTCONF resource paths and `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`
  requests with correct `Accept` and `Content-Type` headers.
- Generate filters and payloads from pyang-inspected model paths.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Include exact XML namespaces and prefixes; never concatenate unescaped XML.
- Use `application/yang-data+json` or `application/yang-data+xml` for modeled
  data as required by the target protocol and server.
- Lock candidate/running only when the server supports it, validate before
  commit, and use confirmed commit/rollback timers for risky changes.
- Keep edit operations explicit (`merge`, `replace`, `create`, `delete`,
  `remove`) and do not use `replace` without a complete subtree.
- Validate payloads against model constraints and device capabilities before
  transmission; distinguish protocol errors from application errors.
- Redact credentials and sensitive leaf values from request/response logs.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Start from the exact YANG module, revision, namespace, operation, datastore, and device capability set. Record list keys and config/state status before writing XML or JSON.

### Phase 2 (Implementation)

Construct namespace-correct payloads and filters with explicit edit operations, list predicates, defaults, and content selection. Reject read-only nodes and unknown namespaces instead of producing plausible XML.

### Phase 3 (Verification)

Validate XML/JSON syntax and model structure locally, then run fixture responses for success, rpc-error, malformed input, and unsupported capability. Compare the payload against the intended tree path.

1. Identify model revision, namespace, datastore, target protocol, and media
   type from capabilities and documentation.
2. Build and locally parse the envelope and payload.
3. Run a read-only GET/filter first, then validate candidate data.
4. Apply edit with lock/commit-confirmed/rollback semantics and verify state.

## Production Code / Template Example

### Input / Requirement

Provide YANG modules or schemas, target revision, operation, datastore, namespace map, desired values, and representative device responses.

### Output / Generated Code

Return the payload or filter, namespace declarations, expected response handling, and a fixture-based validation result.


```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="http://openconfig.net/yang/interfaces">
    <interface>
      <name>Ethernet1</name>
      <config>
        <name>Ethernet1</name>
        <description>managed-by-code</description>
      </config>
    </interface>
  </interfaces>
</config>
```

## Validation, Linting & Testing Commands

- Parse XML with a namespace-aware parser and reject malformed/unknown data.
- Validate JSON/XML against the selected model and compare server state after
  applying changes.
- Test lock contention, validation failure, confirmed-commit expiry, and
  rollback behavior in a lab.
- Run `python3 skills/netconf-restconf-payloads/scripts/validate_json_xml.py`
  and `python3 scripts/validate_skills.py`.

## References

- [RFC 6241 NETCONF](https://www.rfc-editor.org/rfc/rfc6241.html)
- [RFC 8040 RESTCONF](https://www.rfc-editor.org/rfc/rfc8040.html)
- [RFC 7950 YANG 1.1](https://www.rfc-editor.org/rfc/rfc7950.html)

## Offline Execution Contract

Build and parse payloads locally from supplied YANG schemas and fixtures. Without a server, validate XML/JSON syntax and namespaces but do not claim datastore locking, model acceptance, or commit behavior.

## Architecture & Technical Design Patterns

NETCONF uses an outer protocol envelope and a model namespace inside it:

```xml
<nc:edit-config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <nc:target><nc:candidate/></nc:target>
  <nc:config>
    <if:interfaces xmlns:if="http://openconfig.net/yang/interfaces">
      <if:interface><if:name>Ethernet1</if:name></if:interface>
    </if:interfaces>
  </nc:config>
</nc:edit-config>
```

Choose `merge` for partial ownership, `replace` only for a complete owned
subtree, `create` when absence is required, and `delete/remove` according to
the server's supported semantics. RESTCONF uses `/restconf/data/` for data and
`/restconf/operations/` for RPCs; send `Accept` and `Content-Type` matching
`application/yang-data+json` or `application/yang-data+xml`. A safe mutation
sequence is read baseline, lock candidate when supported, edit, validate,
commit-confirmed, verify, then confirm; on failure discard and unlock.
