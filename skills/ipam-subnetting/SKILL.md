---
name: ipam-subnetting
description: "[Tier: Basic] Design and verify hierarchical IPv4/IPv6 VLSM and CIDR allocations, then produce deterministic CSV, JSON, YAML, NetBox, Infoblox, or Terraform seed data. Use this skill when an agent must plan subnets, calculate host capacity, allocate child prefixes, or prove an IP plan has no overlaps before implementation."
license: MIT
compatibility: Python 3.10+ standard library; Terraform/OpenTofu 1.5+ when emitting HCL; optional NetBox or Infoblox API credentials supplied by the user
---

# IPAM Subnetting (Basic)

Produce an IP plan that another engineer can review, validate, import, and
operate. Treat CIDR arithmetic as executable logic: never rely on mental
binary math, approximate host counts, or an unverified model response.

## Core Engineering Capabilities

- Allocate hierarchical IPv4 and IPv6 prefixes from an explicitly supplied
  aggregate using VLSM or fixed-size subnetting.
- Preserve address-family boundaries, parent/child relationships, VRF scope,
  purpose, environment, site, VLAN, and lifecycle metadata.
- Calculate total addresses, usable host capacity, network/broadcast behavior,
  first/last usable addresses, and allocation headroom.
- Emit reviewable JSON/YAML/CSV records and Terraform locals using stable
  names. Generate NetBox or Infoblox seed payloads only when the target
  schema, API version, and authentication contract are known.
- Detect overlaps, duplicate allocations, out-of-parent allocations, invalid
  host bits, mixed IPv4/IPv6 plans, insufficient capacity, and unstable
  ordering before presenting an answer.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

1. **Validate first.** Run `scripts/verify_cidr.py` against the proposed plan
   before returning generated code. The script uses Python `ipaddress`, not
   hand-written binary arithmetic.
2. **Use strict networks.** Input aggregates and prefixes must be canonical
   network addresses. `10.10.0.1/24` is rejected rather than silently changed
   to `10.10.0.0/24`.
3. **Prove containment and disjointness.** Every child must be contained by
   its declared parent, and siblings in the same address-family and VRF must
   not overlap. Identical prefixes in distinct VRFs require explicit VRF
   identity; identical prefixes in one VRF are invalid.
4. **Do not confuse total and usable addresses.** IPv4 traditional subnet
   capacity normally excludes network and broadcast addresses; point-to-point
   links, pools, and IPv6 have different operational conventions. Encode the
   policy explicitly instead of applying one universal subtraction rule.
5. **Keep allocation order stable.** Once a Terraform `cidrsubnets` sequence
   is assigned to real infrastructure, do not reorder or remove existing
   arguments. Append new allocations or use explicit, stable allocation keys.
6. **Separate plan from mutation.** Produce files or API payloads first. Do
   not call NetBox, Infoblox, Terraform, or any device API unless the user
   explicitly requests that mutation and supplies the target context.
7. **Use safe example space.** Examples use RFC 5737 documentation IPv4
   ranges, RFC 3849 documentation IPv6 ranges, or clearly marked private
   ranges. Never echo secrets or production IPAM exports into examples.
8. **Make ambiguity visible.** Ask for or state the missing assumptions:
   parent aggregate, VRF, address family, required hosts, reserved addresses,
   growth factor, site/region, and import target. Do not silently invent a
   production allocation policy.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Collect address pools, site and environment boundaries, required host counts, reserved ranges, IPv4/IPv6 policy, and output consumers. Reject overlapping pools, impossible allocations, and ambiguous reservation rules before calculating subnets.

### Phase 2 (Generation)

Implement deterministic CIDR allocation with explicit ordering, alignment, reservation, and utilization rules. Produce a human-readable plan plus machine-readable records suitable for NetBox, Infoblox, Terraform, or review.

### Phase 3 (Self-Verification)

Run the CIDR verifier against valid, overlap, exhaustion, boundary, and IPv6 cases. Re-run the allocation to prove stability and compare the output with the requested host counts and reserved ranges.

1. **Normalize the request into an allocation model.** Capture the parent
   CIDR, address family, allocation units, required host counts, reserved
   ranges, growth policy, VRF, purpose, and target output format.
2. **Choose an allocation strategy.** Use fixed-size prefixes when every
   segment has the same lifecycle and capacity. Use VLSM when requirements
   differ materially. Prefer explicit subnet IDs for long-lived Terraform
   infrastructure.
3. **Calculate candidate prefixes with a library.** In Python, use
   `ipaddress.ip_network(..., strict=True)`, `subnets()`, `subnet_of()`, and
   `overlaps()`. In Terraform, use `cidrsubnet` or `cidrsubnets` and preserve
   argument order after allocation.
4. **Build records.** Each allocation should include at least `name`,
   `prefix`, `parent`, `family`, `vrf`, `purpose`, `site`, `environment`,
   `status`, and `required_hosts`. Add `usable_hosts` and `reserved` fields
   when the target system needs them.
5. **Run deterministic verification.** Execute:

   ```bash
   python3 skills/ipam-subnetting/scripts/verify_cidr.py plan.json
   ```

   The command exits non-zero on malformed CIDRs, overlaps, duplicate names,
   invalid parentage, family mismatches, or host-capacity violations.
6. **Render the requested artifact.** Keep the canonical plan in JSON or YAML
   and derive CSV, HCL, NetBox, or Infoblox representations from it. Do not
   maintain multiple independently edited sources of truth.
7. **Report assumptions and verification.** State address counts, reserved
   policy, overlap result, source schema, and any fields intentionally left
   for operator review.

## Production Code / Template Example

### Input / Requirement

Provide the parent prefixes, site/environment hierarchy, required hosts, reserved addresses, allocation order, and downstream data format.

### Output / Generated Code

Return the allocation table, machine-readable seed data, utilization summary, and clear errors for overlaps, exhaustion, or invalid prefix boundaries.


### JSON plan input

```json
{
  "aggregates": [{"name": "lab-core", "prefix": "192.0.2.0/24", "vrf": "global"}],
  "allocations": [
    {"name": "web-a", "prefix": "192.0.2.0/26", "parent": "lab-core", "required_hosts": 50, "purpose": "web", "site": "blr-1"},
    {"name": "transit-a", "prefix": "192.0.2.64/30", "parent": "lab-core", "required_hosts": 2, "purpose": "transit", "site": "blr-1"}
  ]
}
```

### Terraform output derived from the plan

```hcl
locals {
  network_cidrs = {
    web_a      = "192.0.2.0/26"
    transit_a  = "192.0.2.64/30"
  }
}
```

Use `cidrsubnet("192.0.2.0/24", 2, 0)` only when the allocation is intended
to remain position-based. For infrastructure with independent lifecycles,
prefer a map of explicit prefixes or stable symbolic keys so adding a subnet
does not renumber existing allocations.

### Capacity policy

For an IPv4 `/26`, report 64 total addresses and 62 conventional host
addresses unless the record declares `is_pool: true`, `point_to_point: true`,
or another documented policy. For IPv6, report total addresses and do not
subtract network/broadcast addresses as an IPv4 convention.

## Validation, Linting & Testing Commands

- Run `python3 scripts/verify_cidr.py <plan.json>` before emitting output.
- Run `python3 scripts/validate_skills.py` from the repository root when
  modifying this skill.
- If Terraform is emitted, run `terraform fmt -check`, `terraform validate`,
  and inspect the plan for unintended address churn.
- If NetBox is the target, verify the aggregate/prefix/VRF mapping against the
  target instance and use its dry-run or staging workflow before POSTing.
- If an import schema is unavailable, stop at a canonical plan and identify
  the missing schema rather than guessing API fields.

## Authoritative References

- Python `ipaddress` API: https://docs.python.org/3/library/ipaddress.html
- Terraform `cidrsubnet` and `cidrsubnets`: https://developer.hashicorp.com/terraform/language/functions/cidrsubnets
- NetBox IPAM hierarchy and VRF behavior: https://netbox.readthedocs.io/en/stable/features/ipam/
- NetBox prefix model: https://netbox.readthedocs.io/en/feature/models/ipam/prefix/
- NetBox REST API: https://netbox.readthedocs.io/en/stable/integrations/rest-api/

## Offline Execution Contract

Use the documented algorithm and Python `ipaddress` verifier without internet access. If Terraform, NetBox, or Infoblox is unavailable, emit canonical JSON/YAML/CSV and clearly mark API-specific fields as unverified; never invent provider syntax.

## Architecture & Technical Design Patterns

Use this canonical plan shape when the user has not supplied one:

```json
{
  "aggregates": [{"name": "site-core", "prefix": "192.0.2.0/20", "vrf": "global"}],
  "allocations": [{"name": "app-a", "prefix": "192.0.2.0/24", "parent": "site-core", "required_hosts": 200, "purpose": "application", "site": "site-a"}]
}
```

Implementation rules: parse every prefix with `ip_network(value, strict=True)`;
use `subnets(prefixlen_diff=n)` for fixed-size partitions; sort by descending
required capacity before VLSM allocation; use `subnet_of()` for parentage and
`overlaps()` for collision checks; compute conventional IPv4 usable capacity
as `max(num_addresses - 2, 0)` only when the record is not a pool or
point-to-point link. A `/31` point-to-point link and IPv6 prefix must use an
explicit policy rather than an automatic IPv4 subtraction.

When emitting Terraform, prefer stable maps:

```hcl
locals {
  subnets = {
    app_a = "192.0.2.0/24"
  }
}
```

Use `cidrsubnet()` only for position-stable allocations. Never insert a new
argument in the middle of an already allocated `cidrsubnets()` call.
