---
name: nso-service-package-development
description: "Design, build, and validate Cisco NSO service packages that model network intent and map it safely to managed devices. Use this skill when creating or changing an NSO package, its service model, templates, callbacks, or package lifecycle."
license: MIT
compatibility: Cisco NSO 5.x or 6.x with compatible NED packages; YANG; Python callbacks optional
---

# NSO Service Package Development (Advanced)

Build NSO service packages as versioned, testable units that model intent, render or compute device changes, and preserve NSO transaction and FASTMAP behavior.

## Core Engineering Capabilities

- Scaffold and organize a service package with metadata, YANG models, templates, Python code when needed, and tests.
- Design service input models with keys, leafrefs, validation constraints, and clear defaults.
- Map service intent to device configuration using XML templates or Python service callbacks.
- Validate package dependencies, NED compatibility, generated configuration, redeploy behavior, and service removal.
- Produce reproducible build and deployment instructions for the target NSO environment.

## Architecture & Technical Design Patterns

- **Model intent first:** Keep service data focused on operator intent. Reference managed devices and shared resources using validated relationships rather than duplicating their configuration.
- **Choose the simplest mapping:** Prefer XML templates for deterministic mappings; use Python FASTMAP callbacks only when the mapping needs logic or allocation that templates cannot express cleanly.
- **Preserve package boundaries:** Keep package metadata, YANG, templates, callbacks, and tests in their expected package locations. Make dependencies and supported NSO/NED versions explicit.
- **Keep mapping transactional:** Apply service changes through NSO's service mapping mechanisms so redeploy, rollback, and removal remain coherent.
- **Design lifecycle behavior:** Specify create, update, redeploy, and delete outcomes before implementing the mapping.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Confirm the NSO release, package skeleton, YANG modules, and NED versions in the target environment. Do not assume callback signatures or package metadata are identical across releases.
- Never place credentials, private keys, or customer configuration in examples, source control, templates, or logs.
- Do not write directly to devices or make out-of-band state changes from a FASTMAP callback. Use supported NSO service mappings and transaction APIs.
- Validate service input and device references before applying changes. Avoid silent defaults that hide invalid or missing intent.
- Ensure keys, generated names, and resource allocations are deterministic and safe to repeat during redeploy.
- Test deletion and rollback as first-class lifecycle paths; a successful create alone does not prove a service is reversible.
- Review native device diffs from a dry-run before committing changes in an operational environment.
- Do not claim that a package has built, loaded, or deployed successfully without running it in a compatible NSO environment.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

1. Collect the NSO version, compatible NEDs, package dependencies, service requirements, target devices, and deployment environment.
2. Define the service inputs, resource ownership, validation rules, generated configuration, and expected create/update/delete behavior.
3. Decide whether XML templates are sufficient or whether Python mapping is necessary; identify any asynchronous lifecycle requirements.
4. Confirm available build tools, package conventions, and test setup before generating package files.

### Phase 2 (Implementation)

1. Create or update the package skeleton using the tooling for the target NSO release.
2. Define the YANG service model and validate references, keys, constraints, and defaults.
3. Implement the mapping using templates or transaction-aware callbacks, with clear vendor/NED-specific branches where needed.
4. Add package metadata and explicit dependencies, then add focused tests and usage documentation.
5. Keep generated artifacts and environment-specific secrets out of source control.

### Phase 3 (Verification)

1. Build the package in the supported NSO development environment and resolve compiler or package-load errors.
2. Test valid and invalid service input, duplicate keys, and missing or incompatible device references.
3. Inspect dry-run/native diffs for create, update, and delete; confirm behavior is idempotent.
4. Exercise redeploy and rollback or removal behavior in a lab, and capture the NSO/NED versions used.
5. Report any behavior that could not be tested because the required NSO or device environment was unavailable.

## Production Code / Template Example

### Input / Requirement

Create a new template-based service package for a target NSO installation. The service should accept explicit intent, validate referenced devices, and produce reviewable native configuration diffs before deployment.

### Output / Generated Code

Start from the package skeleton supported by the target release, for example:

```bash
ncs-make-package --service-skeleton template --dest packages edge-service
```

The resulting package should keep the service model, package metadata, template, and tests together. A typical layout is:

```text
packages/edge-service/
├── package-meta-data.xml
├── src/
│   └── yang/
│       └── edge-service.yang
├── templates/
│   └── edge-service.xml
└── test/
```

Use the generated files and examples for the installed NSO release as the source of truth for exact YANG namespace, servicepoint, metadata, and template syntax. Keep required input fields explicit, reference devices with supported YANG leafrefs, and test the rendered output using the package's supported dry-run workflow before committing.

## Validation, Linting & Testing Commands

- Check the target release's `ncs-make-package --help` and generated package skeleton before relying on command options or file conventions.
- Build the package using its generated build instructions, commonly `make` from the package directory in the NSO development environment.
- Load or reload the package only in a compatible NSO lab or approved development instance.
- Run package tests for validation failures, dry-run diffs, redeploy idempotency, deletion, and rollback.
- Run the repository skill contract check from the repository root:

```bash
python3 scripts/validate_skills.py
```

## Offline Execution Contract

Package source can be scaffolded and reviewed offline, but NSO compilation, package loading, service mapping, and device-native diffs require a compatible NSO environment and NEDs. Without that environment, provide code plus a precise verification checklist and clearly state what remains untested.

## Related Skills

- [nso-xml-templates](../nso-xml-templates/SKILL.md) — Template-based service mappings
- [nso-python-fastmap](../nso-python-fastmap/SKILL.md) — Python-backed FASTMAP callbacks
- [nso-nano-services](../nso-nano-services/SKILL.md) — Asynchronous and multi-stage service plans
- [nso-device-onboarding](../nso-device-onboarding/SKILL.md) — Add and verify managed devices
