---
name: tf-opa-policy
description: "[Tier: Intermediate] Enforce OPA/Conftest policy-as-code over Terraform plans for network resources — deny non-compliant VPC, security group, subnet, ACL, and peering configurations before apply, with scoped rules, explainable denial messages, and CI integration. Use this skill when infrastructure-as-code changes must pass governance checks before they reach a cloud or on-prem network."
license: MIT
compatibility: Terraform 1.3+; OPA 0.50+ or Conftest; terraform plan -json output; Rego; CI pipeline; AWS/Azure/GCP or on-prem Terraform providers; lab or non-production environment for plan testing
---

# Terraform OPA Policy (Intermediate)

Block non-compliant Terraform network changes before apply using OPA/Conftest Rego policies over `terraform plan -json`.

## Core Engineering Capabilities

- Write Rego policies that inspect `terraform plan -json` for network resources: VPCs, subnets, security groups, NACLs, route tables, peering, NAT gateways, and private endpoints.
- Deny rules with explainable messages: public subnets without explicit approval, unrestricted ingress (0.0.0.0/0) on security groups, missing flow logs, unencrypted resources, overly broad NACLs, and unplanned peering.
- Scope policies by environment (dev/staging/prod), resource type, and workspace; allow explicit break-glass overrides with an approver field and audit log.
- Integrate into CI: run `conftest test` or `opa eval` against plan JSON as a pipeline gate; fail the build on deny with resource, rule, and message.
- Generate a compliance report: passed/denied resources, rule hits, and requested changes, stored as a pipeline artifact.
- Test policies offline with synthetic plan JSON covering allow, deny, and edge cases; keep test fixtures separate from production plans.

## Architecture & Technical Design Patterns

```
terraform plan -json
        │
        ▼
   OPA/Conftest + Rego policy bundle
        │
        ▼
  allow/deny decision + explainable messages
        │
        ▼
   CI gate: fail on deny → artifact report
        │
        ▼
   break-glass override (approver + audit)
```

Separate policy data (allowed CIDRs, required tags, approved ports) from policy logic (Rego) so data changes don't require Rego edits. Keep one policy file per concern (e.g., `security_group.rego`, `subnet.rego`, `vpc.rego`) for reviewability. Return structured decisions (`{resource, rule, message, severity}`) rather than booleans only.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Treat OPA as a gate, not a substitute for provider validation: a plan can pass OPA and still fail `terraform apply` due to provider limits, quotas, or dependencies.
- Do not hardcode cloud account IDs, VPC IDs, CIDRs, or approved ports as universal constants; parameterize via policy data and document values as deployment-specific examples.
- Avoid overly permissive break-glass overrides: require an approver, reason, and expiry; log overrides for audit.
- Test policies against real `terraform plan -json` output from the target providers; Rego behavior depends on the plan schema, which varies by Terraform and provider version.
- Keep secrets out of plans and policy data (no hardcoded passwords, keys, or tokens).
- Run policy checks in CI before `terraform apply`; never run apply directly from a plan that has not passed policy.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: Terraform version/providers, target environments/workspaces, network resources in scope, compliance requirements (allowed CIDRs, required tags, encrypted resources, flow logs), break-glass process, and CI integration point.

### Phase 2 (Implementation)

Author Rego policies + data files. Test offline with synthetic plan JSON (allow/deny/edge). Wire `conftest test` / `opa eval` into CI against `terraform plan -json`, failing builds on deny and emitting a compliance report artifact.

### Phase 3 (Verification)

Run CI gate on sample plans (compliant → pass; non-compliant → deny with correct message). Verify break-glass override is logged and requires approver. Confirm a plan that passes OPA can still be reviewed for provider-level issues.

### Input / Requirement

Terraform plan JSON; policy bundle (Rego + data); compliance requirements; CI pipeline.

### Output / Generated Code

Rego policy files, data files, CI gate script, compliance report artifact, and documented override process.

## Production Code / Template Example

```rego
# package network (illustrative Rego; scopes/ports are deployment-specific examples)
package network

deny[msg] {
    resource := input.resource_changes[_]
    resource.change.after.address =~ "aws_subnet.*"
    resource.change.after.map_cidr_block == "0.0.0.0/0"
    msg := sprintf("public subnet %s without explicit approval", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.change.after.type == "aws_security_group"
    rule := resource.change.after.ingress[_]
    rule.cidr_blocks[_] == "0.0.0.0/0"
    msg := sprintf("unrestricted ingress on %s", [resource.address])
}
```

## Validation, Linting & Testing Commands

- `terraform plan -json -out=plan.tfplan && terraform show -json plan.tfplan > plan.json` — produce plan JSON without applying.
- `conftest test -p policy plan.json` or `opa eval -i plan.json -d policy "data.network.deny"` — run policy gate offline.
- Unit tests with synthetic plan JSON: allowed VPC passes; public subnet denied; unrestricted security group denied; missing flow logs denied; break-glass override honored/logged.
- Lint Rego with `opa fmt` and `conftest` where available.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [OPA documentation](https://www.openpolicyagent.org/docs/latest/)
- [Conftest documentation](https://www.conftest.dev/)
- [Terraform plan JSON output](https://developer.hashicorp.com/terraform/internals/plan-json)
- [Rego language reference](https://www.openpolicyagent.org/docs/latest/policy-language/)

## Offline Execution Contract

Policy authoring, Rego formatting, and offline `opa eval`/`conftest test` against synthetic plan JSON require no cloud or live infrastructure. `terraform plan -json` against real providers requires provider credentials and network access; mark provider-specific schema behavior unverified until tested against the target provider version.

## Related Skills

- [tf-aws-networking](../tf-aws-networking/SKILL.md) — Terraform AWS network resources these policies govern
- [tf-azure-gcp-networking](../tf-azure-gcp-networking/SKILL.md) — Azure/GCP network resources in scope
- [tf-module-hardening](../tf-module-hardening/SKILL.md) — hardening that complements policy gates
