---
name: config-scrubber
description: "[Tier: Basic] Scrub network configurations and logs before sharing with agents, vendors, or tickets by replacing secrets and sensitive addresses with deterministic placeholders while preserving topology relationships. Use this skill whenever raw enterprise configuration leaves its controlled system."
license: MIT
compatibility: Python 3.10+ standard library; optional vendor-specific secret patterns; input supplied by the user
---

# Configuration Scrubber (Basic)

Anonymization must preserve enough structure for debugging without preserving
credentials or identifiable production data. Scrubbing is not encryption and
must be reviewed before external sharing.

## Core Engineering Capabilities

- Replace passwords, Type 5/7/8/9 hashes, SNMP communities, BGP/IKE/TACACS
  keys, private keys, tokens, and sensitive hostnames.
- Map public/private addresses to RFC documentation ranges consistently so
  subnet relationships, duplicate detection, and topology remain useful.
- Produce a scrub report listing pattern classes and replacement counts.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use deterministic placeholders and a mapping held only in the controlled
  operator context; never put the reversible map beside the output.
- Fail on private-key blocks, unknown secret-like fields, or binary content
  rather than claiming a clean result.
- Preserve line structure, vendor syntax, comments, and relationships where
  possible, but prefer removing a value over leaking it.
- Do not treat Type 7 or hashed values as safe; they are still sensitive.
- Review the scrubbed artifact manually and scan it again before sharing.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Identify output destination and required topology fidelity.
2. Apply ordered secret/address patterns and collect replacement counts.
3. Scan residual output, review suspicious lines, and publish only the scrubbed
   artifact plus a non-sensitive report.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```text
snmp-server community SuperSecret RO
 -> snmp-server community <SNMP_COMMUNITY_001> RO

interface 10.20.30.1/24
 -> interface 198.51.100.1/24
```

## Validation, Linting & Testing Commands

- Test every secret class, multiline key, repeated value, address mapping,
  false positive, and encoding edge case.
- Search output for known secret markers and private-key boundaries.
- Run `python3 scripts/validate_skills.py`.

## References

- [RFC 5737 documentation IPv4 ranges](https://www.rfc-editor.org/rfc/rfc5737.html)
- [RFC 3849 documentation IPv6 prefix](https://www.rfc-editor.org/rfc/rfc3849.html)

## Offline Execution Contract

Scrubbing must be fully local and deterministic. If a vendor-specific secret pattern is unknown, preserve the line for operator review and fail closed rather than claiming the output is safe to share.

## Architecture & Technical Design Patterns

Apply redaction in ordered passes: private-key blocks and certificates first;
credential-bearing directives second; hashes/tokens/communities third; then
address and hostname pseudonymization. Use a deterministic mapping keyed by
the original value during one run so repeated occurrences remain related, but
do not persist the reversible map with the output. Preserve address-family and
prefix relationships by mapping within a documentation range, not by replacing
each octet independently.

Scan the result for private-key boundaries, password/secret/community/token
markers, known production prefixes, and original sensitive hostnames. Produce
replacement counts and suspicious residual lines. Treat scrubbed output as
still sensitive until a human reviews it; scrubbing is not encryption and
cannot guarantee removal of secrets hidden in comments, binary blobs, or
vendor-specific obfuscation.
