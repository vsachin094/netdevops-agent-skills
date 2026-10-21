---
name: ansible-terraform-role
description: "[Tier: Advanced] Create Ansible roles that wrap Terraform or OpenTofu plan and apply workflows using cloud.terraform modules, plan files, outputs, and add_host handoff. Use this skill when infrastructure provisioning must be reviewed before network or host configuration in one controlled workflow."
license: MIT
compatibility: Ansible Core; cloud.terraform collection; Terraform/OpenTofu; provider credentials; optional CI artifact storage
---

# Ansible Terraform Role (Advanced)

Keep infrastructure provisioning and configuration handoff explicit. Ansible
must inspect a plan before apply and consume typed outputs rather than scrape
Terraform logs or sleep for an assumed completion time.

## Core Engineering Capabilities

- Generate and inspect a Terraform/OpenTofu plan file, apply approved changes,
  read outputs, and add provisioned routers, firewalls, or VMs to Ansible.
- Expose backend, workspace, variable, lock, timeout, and approval controls.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Enforce a two-step plan then apply workflow; never auto-apply an unreviewed
  plan in a general-purpose role.
- Do not use brittle `local-exec` plus `sleep` handoffs. Use provider outputs,
  state locking, and explicit readiness checks.
- Protect state backends, credentials, and sensitive outputs. Mark secret
  outputs sensitive and avoid logging them.
- Make workspace, backend, provider version, and destroy policy explicit.
- Use `add_host` only with validated output schema and stable group/host names.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Initialize/validate workspace and generate plan artifact.
2. Inspect plan summary and require approval according to environment policy.
3. Apply the exact approved plan, collect outputs, and validate readiness.
4. Add hosts/groups and run downstream roles with a recorded handoff.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```yaml
- name: Create reviewed plan
  cloud.terraform.plan_stash:
    project_path: "{{ terraform_project }}"
    plan_file: "{{ plan_path }}"
- name: Apply approved plan
  cloud.terraform.terraform:
    project_path: "{{ terraform_project }}"
    plan_file: "{{ plan_path }}"
    state: present
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Test no-op plan, rejected/destroy plan, lock contention, apply failure,
  sensitive output, and readiness timeout.
- Verify downstream inventory receives only validated outputs.
- Run `ansible-lint`, Terraform validation, and the root validator.

## References

- [cloud.terraform collection](https://galaxy.ansible.com/ui/repo/published/cloud/terraform/)
- [Terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan)
- [Ansible add_host](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/add_host_module.html)

## Offline Execution Contract

Use saved Terraform plan/output fixtures to test schema mapping and inventory handoff. Without Terraform or cloud access, do not claim resource readiness or apply success.

## Architecture & Technical Design Patterns

The role's artifact contract should include project path, backend/workspace,
variable inputs, plan file, plan JSON/summary, approval state, outputs, and
inventory handoff. Generate the plan with the same variables/backend used for
apply; applying a newly generated plan after review defeats approval. Reject a
plan containing destroy/replacement actions unless the environment policy
allows them explicitly.

After apply, read typed outputs, filter sensitive values, and validate required
fields such as IP, hostname, platform, and readiness endpoint. Use
`add_host` only after readiness checks pass, with stable groups and variables.
Store plan/output artifacts securely and never use `local-exec` with a fixed
sleep as a substitute for provider state or a bounded readiness loop.
