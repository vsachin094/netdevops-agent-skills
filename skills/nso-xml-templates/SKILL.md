---
name: nso-xml-templates
description: "[Tier: Intermediate] Create Cisco NSO template-based service packages with `ncs-make-package`, YANG service models, and multi-vendor XML device templates. Use this skill when a deterministic service mapping can be implemented with FASTMAP and template processing instructions."
license: MIT
compatibility: Cisco NSO; compatible NED packages; YANG; XML templates; Python optional for tests
---

# NSO XML Templates (Intermediate)

Model service intent in YANG and map it to device configuration through NSO
templates. The service must be idempotent, reversible, and independent of a
particular device's CLI representation.

## Core Engineering Capabilities

- Scaffold template services with `ncs-make-package --service-skeleton
  template`.
- Define service YANG, device leafrefs, XML templates, variables, `if`,
  `foreach`, and multi-NED mappings.
- Build package tests, dry-run output, service redeploy, and delete behavior.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use strict leafrefs to `/ncs:devices/ncs:device/ncs:name` and validate
  referenced devices before deployment.
- Keep FASTMAP mappings pure and idempotent: the same service intent must
  converge to the same device configuration and `no service` must remove it.
- Use processing instructions only for clear vendor/capability branches;
  avoid one opaque XML template containing unrelated device syntax.
- Never put credentials or generated secrets in templates or service data.
- Test create, modify, delete, redeploy, partial device failure, and NED
  version behavior with `commit dry-run outformat native`.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Define the service input model, NED variants, template variables, tags, device groups, and expected generated config. Identify which fields are optional and what absence means for each device type.

### Phase 2 (Generation)

Generate XML templates with explicit variable paths, loops, conditional branches, and servicepoint ownership. Keep templates idempotent and avoid embedding credentials or device-specific assumptions in generic paths.

### Phase 3 (Self-Verification)

Compile and render the package for each supported NED, then test missing optional data, repeated list entries, invalid references, and delete behavior. Compare the generated config with golden output.

1. Define service model, ownership, device references, and lifecycle.
2. Scaffold package, implement YANG and templates, and compile dependencies.
3. Render dry-run for every supported NED and inspect native output.
4. Test redeploy/delete/rollback and package install/upgrade behavior.

## Production Code / Template Example

### Input / Requirement

Provide service input examples, NED names and versions, variable paths, expected config, and the package compile/render environment.

### Output / Generated Code

Return the XML templates, service mapping, sample inputs, golden output, and package validation commands for every supported NED.


```xml
<config-template xmlns="http://tail-f.com/ns/config/1.0">
  <?if{$DEVICE-NED = 'cisco-ios'}?>
    <ios:interface>
      <ios:name>{$INTERFACE}</ios:name>
      <ios:description>{$DESCRIPTION}</ios:description>
    </ios:interface>
  <?end?>
</config-template>
```

The namespace and NED-specific path must match the installed model; this is a
shape example, not a substitute for generated package validation.

## Validation, Linting & Testing Commands

- Compile YANG and package templates in an NSO development environment.
- Review native dry-run output for every NED and test service deletion.
- Run `check-sync`, package tests, and `python3 scripts/validate_skills.py`.

## References

- [NSO simple service and FASTMAP](https://nso-docs.cisco.com/guides/nso-6.1/development/introduction-to-automation/develop-a-simple-service)
- [NSO service implementation](https://nso-docs.cisco.com/guides/nso-6.4/development/core-concepts/implementing-services)

## Offline Execution Contract

Produce complete YANG/XML package artifacts using supplied NED namespaces and fixtures. Without NSO/NED compilation, validate XML/YANG structure locally and mark native dry-run behavior unverified.

## Architecture & Technical Design Patterns

A template package normally contains `package-meta-data.xml`, `src/yang/<svc>.yang`,
`templates/<svc>.xml`, optional `python/`, and test fixtures. The service YANG
owns input validation and device leafrefs; the XML template maps service data
to `/ncs:devices/ncs:device[ncs:name=...]` through the NED namespace.

Use NSO template variables such as `{$DEVICE}` and processing instructions only
for a tested branch. Keep the mapping idempotent: create and modify must
produce the same desired subtree, while deleting the service removes only the
configuration owned by that service. Test two NEDs with the same service
intent, inspect native dry-run output, then run sync/check-sync and service
delete. Do not embed device credentials, dynamic secrets, or unbounded raw
CLI in XML templates.
