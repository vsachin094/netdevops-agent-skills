---
name: tf-state-surgery
description: "[Tier: Expert] Generate Terraform 1.5+ declarative moved, import, and removed blocks for brownfield adoption, resource renames, and state decomposition with zero-destroy verification. Use this skill when changing state addresses without disrupting live network infrastructure."
license: MIT
compatibility: Terraform 1.5+ or compatible OpenTofu; plan JSON; remote locked state; provider import support; jq/Python optional
---

# Terraform State Surgery (Expert)

Treat state addresses as production identity. Prefer declarative configuration
blocks and a reviewed plan over manual state edits; maintain a recoverable
state backup and a precise mapping from old to new addresses.

## Core Engineering Capabilities

- Generate `moved {}`, `import {}`, and `removed {}` blocks for renames,
  brownfield adoption, and state decomposition.
- Inspect plan JSON and prove the migration has zero destroys before apply.
- Design staged migrations with remote locking, approvals, and rollback.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never edit `terraform.tfstate` directly or use `state push` as a first
  response; use declarative blocks where supported.
- Back up and lock remote state, verify workspace/lineage, and ensure one
  operator owns the migration window.
- Require exact old/new address mapping, provider import identity, and a plan
  with `destroy == 0` unless destruction is explicitly approved.
- Treat `removed` blocks as ownership changes; do not use them to hide drift.
- Do not apply if plan includes replacement, unknown address, provider error,
  or unexpected resource action.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Capture the current state addresses, configuration addresses, provider aliases, workspace/backend, and the exact desired address change. Take a verified state backup and identify resources that must not be destroyed.

### Phase 2 (Implementation)

Generate declarative moved, import, or removed-state operations with the smallest possible scope. Use configuration and state commands appropriate to the Terraform/OpenTofu version; never edit the state file by hand.

### Phase 3 (Verification)

Run state-list and plan checks against a copy or disposable workspace, assert zero unintended destroys, and test missing addresses, provider alias changes, and rollback from the backup.

1. Inventory state addresses and desired configuration.
2. Add moved/import/removed blocks and run plan with JSON output.
3. Run zero-destroy checker, review address mapping and state backup.
4. Apply under lock, inspect state, and remove temporary migration blocks only
   in a later reviewed change when safe.

## Production Code / Template Example

### Input / Requirement

Provide current and desired addresses, resource identity, backend/workspace, provider alias, backup location, and the zero-destroy acceptance condition.

### Output / Generated Code

Return the moved/import/remove declarations or commands, preflight output, expected plan, rollback procedure, and explicit confirmation of any intentional destroy.


```hcl
moved {
  from = module.edge.aws_subnet.old
  to   = module.network.aws_subnet.private["edge"]
}

import {
  to = aws_vpc.main
  id = "vpc-0123456789abcdef0"
}
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Run `terraform plan -out=migration.tfplan` and `terraform show -json`.
- Run `python3 skills/tf-state-surgery/scripts/check_zero_destroy.py plan.json`.
- Verify backup, lock, exact addresses, provider imports, and post-apply state.

## References

- [Terraform moved blocks](https://developer.hashicorp.com/terraform/language/moved)
- [Terraform import blocks](https://developer.hashicorp.com/terraform/language/import)
- [Terraform removed blocks](https://developer.hashicorp.com/terraform/language/resources/syntax#removing-resources)
- [Terraform state locking](https://developer.hashicorp.com/terraform/language/state/backends)

## Offline Execution Contract

Use saved state addresses and plan JSON fixtures to validate mappings and zero-destroy logic. Without the real locked backend/provider, do not claim lineage, import identity, or post-apply state safety.

## Architecture & Technical Design Patterns

Build a state-address mapping table before editing configuration:
`old_address`, `new_address`, `reason`, `provider`, `import_id`, and
`expected_action`. For renames or module moves, use `moved` blocks. For
brownfield adoption, use `import` blocks and verify the provider import ID
format. Use `removed` only when Terraform should stop managing an object while
leaving it in place, and document the new owner.

Run `terraform plan -out=plan.tfplan`, `terraform show -json plan.tfplan`,
then inspect every `resource_changes[*].change.actions`. Permit `no-op`,
`create`, or `update` only when expected; reject `delete` or `replace` for a
zero-downtime migration. Back up and lock the correct remote workspace, verify
lineage/workspace, apply the reviewed plan, and inspect state addresses after
apply. Never hand-edit state JSON or use `-force` casually.
