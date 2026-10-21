---
name: tf-aws-networking
description: "[Tier: Intermediate] Build reusable AWS Terraform networking modules for multi-AZ VPCs, Transit Gateway routing, Direct Connect, Route 53 Resolver, PrivateLink, and Network Firewall. Use this skill when AWS network architecture must be declarative, validated, and consistently tagged."
license: MIT
compatibility: Terraform/OpenTofu; hashicorp/aws provider; AWS credentials; tflint/checkov optional
---

# Terraform AWS Networking (Intermediate)

Model AWS routing and security as explicit graph relationships. A module is
not complete until route-table associations, logging, propagation, and
failure-domain behavior are reviewable.

## Core Engineering Capabilities

- Generate multi-AZ VPCs, subnets, TGW hubs/spokes, Direct Connect VIFs,
  Resolver endpoints, PrivateLink, and Network Firewall policy modules.
- Use CIDR/ASN validation, stable `for_each` keys, flow logs, tags, and
  explicit route associations.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Validate CIDRs, ASN ranges, AZ counts, and mutually exclusive routing modes.
- Keep `aws_vpc_security_group_ingress_rule` and egress rules standalone;
  avoid ambiguous inline rule churn.
- Enable VPC Flow Logs by default unless a documented exception exists.
- Model TGW route tables and propagation/associations explicitly; never assume
  attachment implies reachability.
- Keep provider credentials external and mark sensitive outputs.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Collect account and region boundaries, availability zones, VPC and subnet CIDRs, routing intent, TGW or Direct Connect requirements, DNS behavior, and firewall ownership. Record provider and module versions.

### Phase 2 (Implementation)

Generate stable Terraform/OpenTofu modules with explicit maps for VPCs, subnets, route tables, attachments, Resolver, and firewall resources. Keep state ownership and cross-account dependencies visible.

### Phase 3 (Verification)

Run fmt, validate, plan, policy checks, and fixture tests for overlapping CIDRs, missing AZs, route conflicts, deletion protection, and provider errors. Never infer a successful apply from plan output.

1. Define regions/AZs, CIDRs, routing domains, inspection path, and ownership.
2. Render plan and inspect route graph, security, logs, and replacements.
3. Validate with AWS provider and policy scans, then apply in stages.

## Production Code / Template Example

### Input / Requirement

Provide AWS account/region scope, CIDR plan, AZs, connectivity requirements, DNS and security intent, state backend, and provider constraints.

### Output / Generated Code

Return the module inputs, resources, outputs, plan expectations, policy checks, and a test matrix for create, update, and removal.


```hcl
resource "aws_ec2_transit_gateway_route_table_association" "spoke" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.spoke.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.core.id
}
```

## Validation, Linting & Testing Commands

- Run fmt, validate, tflint, checkov, and reviewed plan.
- Test missing route association, asymmetric propagation, log failure, and
  multi-AZ subnet map changes.
- Run `python3 scripts/validate_skills.py`.

## References

- [AWS provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS VPC](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)

## Offline Execution Contract

Use local provider schemas, mocked plans, and route-graph fixtures. Without AWS credentials or provider plugins, generate reviewed HCL and expected relationships but do not claim AWS acceptance or reachability.

## Architecture & Technical Design Patterns

For a multi-AZ AWS design, model `az -> public/private subnet -> route table`
as explicit maps. A TGW design additionally needs `attachment -> TGW route
table association -> propagation -> destination route`. A VPC attachment alone
does not create transitive reachability. Direct Connect requires explicit
virtual interface, allowed prefixes, and route-domain ownership; Resolver
endpoints require subnet placement and security-group rules.

Enable VPC Flow Logs with a defined destination and retention. Use standalone
security-group ingress/egress resources so rule identity is stable. Validate
CIDR overlap, subnet capacity, AZ count, TGW route propagation, inspection
paths, NAT placement, and asymmetric routing. Use provider data sources for
existing shared infrastructure rather than recreating it from guessed IDs.
