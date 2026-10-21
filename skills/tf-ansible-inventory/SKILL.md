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

Define the Terraform/OpenTofu outputs, host identity, group rules, sensitive values, inventory format, and the point at which Ansible consumes the result. Check output types before generating inventory data.

### Phase 2 (Generation)

Generate a deterministic inventory adapter that maps declared outputs to hosts, groups, and vars without leaking sensitive outputs. Preserve stable ordering and distinguish an empty inventory from a failed plan.

### Phase 3 (Self-Verification)

Run fmt, validate, plan fixtures, inventory rendering, and Ansible parse checks. Test missing outputs, duplicate hosts, sensitive values, empty groups, and a second rendering for stable diffs.

1. Define output contract and inventory mapping.
2. Apply infrastructure, collect outputs, validate readiness, and render.
3. Run `ansible-inventory --list`, then configure only validated hosts.

## Production Code / Template Example

### Input / Requirement

Provide Terraform/OpenTofu output definitions, desired inventory schema, group and variable rules, sensitivity policy, and the downstream Ansible command.

### Output / Generated Code

Return the handoff code or template, output fixtures, generated inventory, sensitivity checks, and an end-to-end parse test.


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
