---
name: acl-cis-compliance
description: "[Tier: Advanced] Audit network configurations against CIS-style controls and analyze ACL/firewall policies for shadowed, redundant, and overly permissive rules, then generate idempotent remediation playbooks. Use this skill when compliance and policy correctness must be proven before remediation."
license: MIT
compatibility: Python 3.10+; vendor config parsers; Ansible; optional Batfish; CIS benchmark/version and target platform documentation
---

# ACL/CIS Compliance (Advanced)

Separate detection, evidence, recommendation, and remediation. A scanner must
not silently change policy, and a remediation must preserve ordering and the
management path.

## Core Engineering Capabilities

- Check SSHv2, AAA/TACACS fallback, SNMPv3 authPriv, CoPP, logging, and secure
  management controls against versioned policies.
- Detect ACL shadowing, redundancy, broad permits, unreachable rules, and
  ordering errors across supported policy dialects.
- Generate reviewed, idempotent Ansible remediation with evidence links.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Version CIS controls and map each finding to exact config evidence and
  severity; do not claim benchmark compliance from generic keywords.
- Preserve top-down most-specific ordering and distinguish IPv4/IPv6,
  direction, interface, VRF, and implicit deny semantics.
- Treat `permit ip any any`, management permits, and CoPP changes as high-risk;
  require explicit impact analysis and approval.
- Never auto-remediate when parser confidence is low or policy intent is
  ambiguous. Keep remediation reversible and check-mode safe.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Start with the platform, ACL direction, interface or zone, CIS baseline, and the intended traffic matrix. Parse the supplied ACLs into ordered entries and stop if object names, address groups, or service definitions are missing.

### Phase 2 (Generation)

Build a normalized rule model, then calculate shadowing, redundancy, overly broad matches, and explicit exceptions. Produce findings with line references and a minimal remediation diff; preserve rule order and default-deny behavior.

### Phase 3 (Self-Verification)

Run the bundled shadow-analysis helper against clean, shadowed, duplicate, and malformed fixtures. Review every proposed permit or deny change against the traffic matrix before treating the report as actionable.

1. Scrub and parse config, identify platform/version, and collect evidence.
2. Evaluate controls and ACL relations, then produce findings with confidence.
3. Generate remediation, run check/diff and pre/post connectivity checks, and
   apply only after approval.

## Production Code / Template Example

### Input / Requirement

Provide sanitized ACL text, platform syntax, direction and attachment point, the compliance baseline, and the approved traffic matrix. State which rules are intentional exceptions.

### Output / Generated Code

Return a findings report with severity, evidence, affected rule, and remediation. When remediation is requested, generate a reviewable patch and a regression fixture for every changed decision.


```text
Finding: ACL-003
Severity: high
Evidence: line 42 permit ip any any
Impact: unrestricted transit in inbound WAN direction
Remediation: replace with approved service prefixes; operator approval required
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Test shadow, duplicate, subset, exception, IPv6, implicit-deny, and rule
  reorder cases.
- Validate remediation in a lab/digital twin and assert management reachability.
- Run `python3 skills/acl-cis-compliance/scripts/detect_shadowed_acls.py` and
  the root validator.

## References

- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [Batfish ACL questions](https://batfish.readthedocs.io/en/latest/)

## Offline Execution Contract

Run checks against sanitized configs and local policy fixtures. Without vendor parsers or a live device, report findings with confidence and evidence requirements; never auto-remediate ambiguous syntax.

## Architecture & Technical Design Patterns

Normalize an ACL rule into `id`, `family`, `direction`, `interface/zone`,
`protocol`, `source`, `destination`, `ports`, `action`, `log`, and `sequence`.
Evaluate shadowing in order: rule B is shadowed by rule A when A's match set
contains B's match set and both actions are terminal for the same context.
Exact duplicates are redundant; a broad permit before a specific deny is a
high-severity policy finding. Preserve implicit deny and vendor-specific
evaluation semantics.

Each CIS finding needs control ID/version, severity, evidence lines, parser
confidence, remediation, verification, and exception owner/expiry. Generate
remediation only from a known platform mapping, preserve rule order, run
check-mode/diff, and verify management reachability plus intended traffic in a
lab or digital twin before applying.
