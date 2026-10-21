---
name: tf-firewall-policies
description: "[Tier: Advanced] Automate enterprise firewall policies with Terraform providers for Palo Alto, Fortinet, Check Point, and Cloudflare using external YAML rule data. Use this skill when security policy must be stable-keyed, reviewable, logged, and safe under rule insertion/deletion."
license: MIT
compatibility: Terraform/OpenTofu; target firewall provider; YAML; yamldecode; checkov/tflint optional
---

# Terraform Firewall Policies (Advanced)

Firewall rule order and identity are security state. Model rules with stable
keys, explicit ordering, object reuse, and logging; never let a list index
renumber production policy accidentally.

## Core Engineering Capabilities

- Load external YAML with `yamldecode`, validate rule objects, and create
  provider resources with `for_each`.
- Manage address/service objects, rule ordering, logging, hit counters, and
  policy attachments across supported firewalls.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use stable map keys, not `count` indexes, for rules and objects. Deleting a
  rule must not rename every later rule.
- Default to deny or the platform-approved secure posture; require explicit
  source, destination, service, action, logging, and owner fields.
- Reuse object groups, validate shadow/redundant rules, and require review for
  broad `any` or `permit` changes.
- Keep secrets, certificates, and tokens external; mark sensitive outputs.
- Plan and inspect rule order and provider behavior before apply.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Validate YAML schema, stable IDs, order, and object references.
2. Generate plan and run policy analysis for shadow/redundant/broad rules.
3. Review logs and hit counters, apply, and verify policy attachment.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```hcl
locals { rules = yamldecode(file("rules.yaml")).rules }
resource "provider_firewall_rule" "this" {
  for_each = { for rule in local.rules : rule.id => rule }
  name     = each.key
  action   = each.value.action
}
```

## Validation, Linting & Testing Commands

- Test insertion/deletion, duplicate IDs, shadowing, `any`, object deletion,
  logging disabled, and provider ordering.
- Run fmt, validate, policy scan, and reviewed plan.
- Run `python3 scripts/validate_skills.py`.

## References

- [Terraform `yamldecode`](https://developer.hashicorp.com/terraform/language/functions/yamldecode)
- [Terraform `for_each`](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

## Offline Execution Contract

Validate YAML rule schema, stable keys, ordering, and shadow analysis locally. Without a firewall provider or appliance, generate policy HCL and a review diff but do not claim policy installation or enforcement.

## Architecture & Technical Design Patterns

Use a rule object with stable `id`, `position`, `source`, `destination`,
`services`, `action`, `log`, `owner`, `ticket`, and `enabled` fields. Convert
the YAML list to a map by `id` for `for_each`; keep ordering as an explicit
provider-supported position or a separately validated sequence. Validate
duplicate IDs, unknown object references, invalid CIDRs, empty service sets,
shadowed rules, and broad `any` values.

Before apply, produce a normalized rule table showing effective source,
destination, service, action, order, and logging. Require explicit approval for
insertions above existing permits, deny-to-permit changes, management access,
and object deletion. After apply, verify policy attachment, compilation,
logging, and hit counters using the provider/API or a lab fixture.
