---
name: tf-module-hardening
description: "[Tier: Advanced] Harden Terraform/OpenTofu modules for tflint, Trivy, Checkov, provider pinning, encrypted state, sensitive values, lifecycle preconditions, and native Terraform or Terratest suites. Use this skill when a module is approaching production or needs a security/compliance gate."
license: MIT
compatibility: Terraform/OpenTofu; tflint; Trivy; Checkov; Go/Terratest optional; CI runner
---

# Terraform Module Hardening (Advanced)

Make insecure or ambiguous infrastructure fail before apply. Security scans
are complementary to semantic validation and must not replace plan review.

## Core Engineering Capabilities

- Pin providers/modules, harden backend and secrets, add pre/postconditions,
  and generate unit/integration tests.
- Run formatting, validation, lint, security, policy, and zero-destroy gates.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Commit `.terraform.lock.hcl`; pin provider versions and review upgrades.
- Use encrypted remote state with locking and least-privilege access.
- Mark secrets `sensitive = true`, but still protect state because sensitive
  values can exist in state.
- Add lifecycle `precondition`/`postcondition` for network invariants and
  fail on invalid provider results.
- Avoid broad `-auto-approve`, `-target`, and destructive exceptions in CI.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Inventory providers, state, secrets, resources, and invariants.
2. Add constraints and tests, then run all static/security checks.
3. Review plan and apply only through an approved pipeline.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```hcl
lifecycle {
  precondition {
    condition     = var.enable_public == false || length(var.allowed_cidrs) > 0
    error_message = "Public exposure requires explicit allowed CIDRs."
  }
}
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Run `terraform fmt -check`, validate, tflint, Trivy, Checkov, and native
  tests/Terratest.
- Include negative tests for public exposure, unencrypted state, unpinned
  provider, and missing tags.
- Run `sh skills/tf-module-hardening/scripts/validate_tf.sh`.

## References

- [Terraform validation](https://developer.hashicorp.com/terraform/language/validate)
- [Terraform state security](https://developer.hashicorp.com/terraform/language/state)
- [Terraform provider lock file](https://developer.hashicorp.com/terraform/language/files/dependency-lock)

## Offline Execution Contract

Run local static checks against supplied code and lock files. If Terraform, tflint, Trivy, or Checkov is unavailable, report each skipped gate and never replace a security result with an assumption of compliance.

## Architecture & Technical Design Patterns

Use a layered gate: `terraform fmt -check`, `init -backend=false`,
`validate`, provider lock review, `tflint`, Checkov/Trivy, unit tests, plan
policy, then integration tests. Pin providers in `required_providers` and
commit `.terraform.lock.hcl`; do not use unconstrained ranges for production
without an upper compatibility policy.

Add variable validation for CIDRs, regions, names, and enums. Add resource
preconditions for assumptions and postconditions for provider guarantees, but
remember that a failed postcondition stops downstream work and does not undo
already-created resources. Mark outputs sensitive, protect remote encrypted
state with locking and least privilege, and scan plans/state artifacts for
secrets before publishing.
