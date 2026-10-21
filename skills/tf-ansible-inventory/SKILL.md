---
name: tf-ansible-inventory
description: "[Tier: Intermediate] Connect Terraform/OpenTofu outputs to Ansible through cloud.terraform resources or structured YAML inventory generation. Use this skill when newly provisioned routers, firewalls, VMs, or hosts must enter a configuration workflow without brittle provisioner hacks."
license: MIT
compatibility: Terraform/OpenTofu; Ansible Core; cloud.terraform collection optional; YAML/JSON inventory
---

# Terraform to Ansible Inventory (Intermediate)

Make the infrastructure-to-configuration handoff typed and explicit. Treat
Terraform outputs as an API with stable keys and sensitivity metadata.

## Core Engineering Capabilities

- Emit Ansible inventory via `local_file`, cloud.terraform inventory resources,
  or a CI artifact.
- Map Terraform outputs to `ansible_host`, groups, connection variables, and
  readiness checks.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Do not use `local-exec` plus arbitrary sleeps as a readiness mechanism.
- Keep generated inventory out of source control when it contains addresses or
  secrets; mark sensitive outputs and redact logs.
- Validate output schema, stable host IDs, group names, and connection data
  before invoking Ansible.
- Wait on explicit health/SSH/API readiness with bounded retries and report
  non-ready resources separately.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define output contract and inventory mapping.
2. Apply infrastructure, collect outputs, validate readiness, and render.
3. Run `ansible-inventory --list`, then configure only validated hosts.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```hcl
output "network_hosts" {
  value = { for k, vm in aws_instance.router : k => { ip = vm.private_ip, role = "router" } }
}
```

## Validation, Linting & Testing Commands

- Test no hosts, duplicate keys, sensitive output, readiness timeout, and
  destroyed resources.
- Run Terraform plan/validate and `ansible-inventory --list`.
- Run `python3 scripts/validate_skills.py`.

## References

- [Terraform outputs](https://developer.hashicorp.com/terraform/language/values/outputs)
- [Ansible inventory guide](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html)

## Offline Execution Contract

Use saved Terraform outputs to generate and validate inventory locally. Without Terraform or Ansible, test the output schema and readiness contract; never invent hosts or report infrastructure as ready.

## Architecture & Technical Design Patterns

Define an output schema such as:

```json
{"routers": {"edge-1": {"ansible_host": "192.0.2.10", "ansible_network_os": "cisco.ios.ios", "site": "a"}}}
```

Use Terraform outputs for stable identity, address, platform, role, and
credential reference only. Render inventory with JSON/YAML or a supported
Terraform/Ansible integration; do not scrape `terraform apply` text. After
provisioning, perform bounded SSH/API readiness checks, then run
`ansible-inventory --list --graph` and assert host/group counts. Treat missing
or sensitive outputs as schema failures and keep generated inventories out of
source control when they contain infrastructure details.
