---
name: tf-vpc-foundations
description: "[Tier: Basic] Generate foundational Terraform/OpenTofu VPC/VNet modules with subnets, gateways, routes, security groups, and remote state. Use this skill when creating a reusable cloud network baseline with validated inputs and clear main/variables/outputs/versions separation."
license: MIT
compatibility: Terraform/OpenTofu; cloud provider SDK; tflint optional; provider credentials supplied externally
---

# Terraform VPC Foundations (Basic)

Build a small, composable module that owns network primitives and exposes
stable outputs. Keep CIDRs, credentials, provider versions, and state backend
configuration separate from resources.

## Core Engineering Capabilities

- Generate VPC/VNet, public/private subnet, route, internet/NAT gateway, and
  security-group resources.
- Use `cidrsubnet`/`cidrsubnets`, variable validation, tags, outputs, and
  encrypted remote state backends.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Separate `main.tf`, `variables.tf`, `outputs.tf`, and `versions.tf`.
- Never hardcode credentials or CIDR literals inside resource blocks; expose
  validated variables and stable maps.
- Require non-overlapping address ranges, explicit availability zones, and
  intentional public exposure.
- Enable flow logs and least-privilege security rules where the provider
  supports them.
- Use remote, encrypted, locked state for shared environments and exclude
  state/plan artifacts from Git.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Define the network intent, cloud and region, parent CIDR, subnet tiers, route domains, security boundaries, NAT/DNS requirements, state backend, and ownership of shared resources.

### Phase 2 (Generation)

Generate reusable VPC/VNet modules with stable maps, explicit route and security relationships, validated CIDRs, provider constraints, and outputs that downstream inventory can consume.

### Phase 3 (Self-Verification)

Run fmt, validate, plan, and policy tests for overlap, missing routes, invalid subnet sizes, accidental public exposure, and safe removal. Compare a second plan for no-op behavior.

1. Define network contract and CIDR allocation.
2. Validate variables and generate plan.
3. Review routes, exposure, NAT, flow logs, and destroy actions.
4. Apply only through approved state backend and verify outputs.

## Production Code / Template Example

### Input / Requirement

Provide cloud, region, CIDR plan, subnet tiers, route requirements, security intent, state policy, provider version, and required outputs.

### Output / Generated Code

Return module inputs, resources, outputs, example intent, plan expectations, and tests for create, update, no-op, and removal scenarios.


```hcl
variable "base_cidr" {
  type = string
  validation { condition = can(cidrnetmask(var.base_cidr)) error_message = "Must be CIDR." }
}

locals { private_cidrs = cidrsubnets(var.base_cidr, 4, 4, 4) }
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Run `terraform fmt -check`, `terraform init`, `terraform validate`,
  `tflint`, and a reviewed `terraform plan`.
- Test invalid CIDRs, overlap, missing zones, no-op plan, and accidental
  public exposure.
- Run `sh skills/tf-vpc-foundations/scripts/validate_tf.sh`.

## References

- [Terraform CIDR functions](https://developer.hashicorp.com/terraform/language/functions/cidrsubnets)
- [Terraform state and locking](https://developer.hashicorp.com/terraform/language/state/backends)

## Offline Execution Contract

Generate provider-neutral HCL, variable validation, and plan fixtures offline. Without Terraform/provider plugins, validate syntax and module contracts only; do not claim cloud resource behavior.

## Architecture & Technical Design Patterns

Use a module interface with `name`, `region`, `base_cidr`, `availability_zones`,
`public_subnets`, `private_subnets`, `enable_nat`, `enable_flow_logs`, and
`tags`. Validate that every child CIDR is inside the base, children do not
overlap, AZ keys are unique, and public exposure is explicit. Prefer maps keyed
by semantic names (`public-a`, `private-a`) over lists indexed by position.

Keep resource ownership clear: the VPC module owns network primitives and
outputs IDs/CIDRs; workload modules consume those outputs and own instances or
services. Route tables must be associated explicitly. Security groups should
use least-privilege standalone rules and never contain credentials. Plan
review must inspect route targets, internet/NAT paths, flow logs, replacements,
and any destroy action before apply.
