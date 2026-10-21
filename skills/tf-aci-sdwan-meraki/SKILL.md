---
name: tf-aci-sdwan-meraki
description: "[Tier: Advanced] Automate controller-based networks with Terraform for Cisco ACI, Catalyst SD-WAN, Meraki, and Arista CloudVision using stable YAML-driven policy maps. Use this skill when controller objects have hierarchical dependencies and must be deployed consistently at scale."
license: MIT
compatibility: Terraform/OpenTofu; target controller provider; YAML/JSON; controller credentials externalized
---

# Terraform ACI/SD-WAN/Meraki (Advanced)

Respect the controller's object hierarchy and asynchronous behavior. A resource
being accepted by an API does not prove that dependent fabric policy is ready.

## Core Engineering Capabilities

- Model ACI tenants, VRFs, bridge domains, EPGs, contracts, SD-WAN policy,
  Meraki networks/devices, and CloudVision policies.
- Use stable `for_each` maps, explicit dependencies, YAML intent, and outputs
  suitable for downstream inventory and validation.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Preserve ACI Tenant→VRF→BD→EPG→contract relationships and validate every
  reference before plan.
- Avoid provider-specific list indexes; use stable IDs and names.
- Keep controller tokens external, mark secrets sensitive, and avoid logging
  API responses that include credentials.
- Model asynchronous readiness and eventual consistency with provider-supported
  mechanisms, not arbitrary sleeps.
- Plan policy changes and verify controller health, fabric faults, and intended
  attachment after apply.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Record the controller type and version, provider version, account or organization scope, object hierarchy, state backend, and asynchronous readiness signals. Confirm which resources are authoritative and which are generated dependencies.

### Phase 2 (Implementation)

Model controller objects with stable for_each keys, explicit parent dependencies, YAML intent, sensitive variables, and provider-supported readiness behavior. Keep ACI, SD-WAN, Meraki, and CloudVision differences behind clear resource boundaries.

### Phase 3 (Verification)

Run fmt, validate, plan, and provider tests with mocked or lab controller responses. Test duplicate keys, parent deletion, eventual consistency, rejected policy, and post-apply health or fault checks.

1. Define hierarchy, ownership, dependencies, and stable IDs.
2. Validate YAML intent and generate plan.
3. Apply in dependency order, poll supported readiness, and run postchecks.

## Production Code / Template Example

### Input / Requirement

Provide controller type and version, provider constraints, hierarchy, YAML intent, backend policy, and the plan or post-apply evidence required for acceptance.

### Output / Generated Code

Return the Terraform/OpenTofu module, intent data, provider constraints, plan output expectations, and controller-specific postchecks.


```hcl
locals { epgs = yamldecode(file("fabric.yaml")).epgs }
resource "aci_application_epg" "this" {
  for_each = { for epg in local.epgs : "${epg.tenant}/${epg.app}/${epg.name}" => epg }
  name = each.value.name
}
```

## Validation, Linting & Testing Commands

- Test hierarchy references, duplicate keys, dependency deletion, controller
  faults, and eventual consistency.
- Run provider validation, plan review, and controller postchecks.
- Run `python3 scripts/validate_skills.py`.

## References

- [Cisco ACI Terraform provider](https://registry.terraform.io/providers/CiscoDevNet/aci/latest/docs)
- [Cisco Meraki Terraform provider](https://registry.terraform.io/providers/meraki/meraki/latest/docs)
- [Arista CloudVision provider](https://registry.terraform.io/providers/arista/cvp/latest/docs)

## Offline Execution Contract

Use local YAML intent, provider schemas, and mocked controller responses. Without a controller, generate hierarchy-safe configuration and postcheck plans while explicitly leaving asynchronous readiness unverified.

## Architecture & Technical Design Patterns

Treat controller resources as a dependency graph. For ACI the normal chain is
tenant -> VRF -> bridge domain -> application profile -> EPG -> contract/filter
-> domain/static path; for SD-WAN it is organization/site/device -> feature
templates -> device templates -> policy/attachment; for Meraki it is
organization -> network -> device -> switch/SSID/firewall policy. Use stable
semantic keys such as `tenant/app/epg`, never list indexes.

Validate parent references before plan, model provider eventual consistency
with supported readiness/status fields, and preserve controller ownership
boundaries. A successful API response only proves acceptance; postchecks must
inspect faults, policy attachment, device status, and effective configuration.
Do not destroy a parent resource while children still reference it unless the
provider dependency graph and migration plan explicitly support it.
