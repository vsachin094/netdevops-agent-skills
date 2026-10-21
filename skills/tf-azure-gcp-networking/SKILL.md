---
name: tf-azure-gcp-networking
description: "[Tier: Intermediate] Build Azure and GCP Terraform modules for hub-spoke networking, Virtual WAN, VNet peering, ExpressRoute, Azure Firewall, Shared VPC, Cloud Router, Cloud NAT, NCC, and private DNS. Use this skill when multi-cloud network topology must share consistent validation and tagging."
license: MIT
compatibility: Terraform/OpenTofu; azurerm and/or hashicorp/google providers; cloud credentials; tflint/checkov optional
---

# Terraform Azure/GCP Networking (Intermediate)

Keep provider-specific routing and security semantics explicit while presenting
consistent module interfaces for CIDRs, regions, tags, logging, and ownership.

## Core Engineering Capabilities

- Generate Azure hub/spoke/VWAN, peering, ExpressRoute, Firewall, and DNS
  Resolver resources.
- Generate GCP Shared VPC, Cloud Router/NAT, Network Connectivity Center,
  custom routes, and private DNS resources.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use provider-appropriate CIDR/ASN validation and explicit route table or
  peering associations.
- Enable flow logs, diagnostics, firewall logging, and consistent tags/labels
  by default where supported.
- Model transitive routing deliberately; Azure VNet peering and GCP custom
  routes do not imply every desired path.
- Keep project/subscription, region, and identity inputs explicit and secret-
  free. Never embed cloud credentials in provider blocks.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Separate Azure and GCP requirements: subscriptions/projects, regions, hub and spoke CIDRs, routing, NAT, DNS, identity, and firewall ownership. Record provider versions and cross-cloud connectivity assumptions.

### Phase 2 (Implementation)

Generate cloud-specific modules with stable keys and explicit dependencies while keeping the shared intent model provider-neutral. Avoid copying Azure semantics into GCP resources or vice versa.

### Phase 3 (Verification)

Run fmt, validate, plan, and policy checks for each provider. Test overlapping CIDRs, missing identity permissions, route propagation, NAT edge cases, and safe removal using fixtures or provider mocks.

1. Define cloud boundary, hub/spoke ownership, address plan, and inspection.
2. Validate provider-specific topology and generate plan.
3. Review route tables, firewall, DNS, logging, and replacement behavior.
4. Apply in dependency order and test cross-cloud reachability.

## Production Code / Template Example

### Input / Requirement

Provide cloud, subscription or project, regions, CIDR plan, hub/spoke topology, routing and DNS intent, identity constraints, and state policy.

### Output / Generated Code

Return provider-specific modules, shared intent examples, plan expectations, policy tests, and a matrix of cloud features that are supported or rejected.


```hcl
variable "address_space" {
  type = string
  validation { condition = can(cidrhost(var.address_space, 0)) error_message = "Invalid CIDR." }
}
```

## Validation, Linting & Testing Commands

- Run provider validation, fmt, tflint, checkov, and plan review.
- Test peering removal, route propagation, NAT exhaustion, and firewall log
  behavior in a non-production subscription/project.
- Run `python3 scripts/validate_skills.py`.

## References

- [AzureRM provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Google provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

## Offline Execution Contract

Use supplied provider schemas and fixtures to validate topology relationships. Without cloud plugins or credentials, produce plan-ready modules and identify provider-specific behavior that remains unverified.

## Architecture & Technical Design Patterns

Keep Azure subscription/resource-group/region and GCP project/region/network
inputs explicit. In Azure, model hub/spoke VNet peering, route tables, next
hops, firewall, private DNS, and gateway transit as separate relationships;
peering does not automatically provide every transitive route. In GCP, model
Shared VPC host/service projects, custom routes, Cloud Router ASN/BGP, Cloud
NAT, and NCC spokes explicitly; Cloud NAT does not provide inbound reachability.

Use provider-specific validation for CIDRs, ASNs, regions, and names. Add
diagnostic/flow logging, consistent tags/labels, explicit DNS links, and
dependency order. Plan review must check route propagation, firewall direction,
private endpoint DNS, cross-project/subscription ownership, and replacement
impact before apply.
