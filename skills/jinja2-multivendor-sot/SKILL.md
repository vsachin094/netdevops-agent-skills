---
name: jinja2-multivendor-sot
description: "[Tier: Intermediate] Design modular multi-vendor Jinja2 template hierarchies driven by one vendor-agnostic YAML source of truth. Use this skill when the same network intent must render consistently for IOS-XE, NX-OS, EOS, Junos, or other explicitly supported platforms."
license: MIT
compatibility: Python 3.10+; Jinja2 3+; YAML; vendor capability data; optional pytest
---

# Jinja2 Multi-Vendor SoT (Intermediate)

Use one intent model and explicit platform adapters. Vendor templates should
express syntax differences, not redefine the network design.

## Core Engineering Capabilities

- Organize base templates, macros, includes, and vendor directories for
  interfaces, VLANs, routing, AAA, telemetry, and services.
- Select platform/version templates from validated device metadata.
- Render deterministic multi-device artifacts with `StrictUndefined` and
  capability-aware branches.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Keep source-of-truth data free of vendor CLI strings and keep vendor syntax
  out of shared intent fields.
- Use `{% include %}`, `{% extends %}`, and macros for composition; avoid
  copy/paste vendor templates that drift independently.
- Validate platform, version, required capabilities, and data schema before
  selecting a template. Unsupported combinations must fail clearly.
- Use stable ordering for interfaces, VLANs, peers, and policies so diffs are
  meaningful. Never use unordered set iteration in rendered output.
- Do not hide semantic differences behind a common variable name. Model them
  as capabilities or explicit vendor-specific fields.
- Render to files per device and platform; never concatenate different vendor
  configuration into one artifact.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Define the canonical source-of-truth model, vendor capability differences, required defaults, and unsupported features. Confirm which fields are authoritative and which are derived per platform.

### Phase 2 (Generation)

Build vendor-specific renderers behind one normalized model, using capability maps or explicit adapter templates instead of scattered vendor conditionals. Make unsupported combinations fail with the platform and field named.

### Phase 3 (Self-Verification)

Render the same intent for each supported vendor, compare golden outputs, test capability gaps and empty collections, and parse or lint the results with platform-aware checks.

1. Define the vendor-neutral model and capability matrix.
2. Build shared macros and one vendor implementation with golden fixtures.
3. Add additional vendors only after confirming syntax and semantic mapping.
4. Render all supported fixtures, compare diffs, and run vendor validation.

## Production Code / Template Example

### Input / Requirement

Provide canonical intent data, target vendors and versions, capability matrix, expected output differences, and the platform validation tools available locally.

### Output / Generated Code

Return the shared model, vendor templates or adapters, capability declarations, golden outputs, and a matrix of supported and rejected features.


```text
templates/
  base/interface.j2
  iosxe/interfaces.j2
  nxos/interfaces.j2
  eos/interfaces.j2
  junos/interfaces.j2
```

```python
template = f"{device['platform']}/interfaces.j2"
rendered = env.get_template(template).render(device=device, intent=intent)
```

The platform selector must come from a validated allow-list, not a path built
from raw user input.

## Validation, Linting & Testing Commands

- Render every vendor fixture using strict undefined handling.
- Check golden output, syntax validation, stable ordering, and unsupported
  capability failures.
- Test an empty optional section and a missing required field for each vendor.
- Run `python3 scripts/validate_skills.py`.

## References

- [Jinja template designer documentation](https://jinja.palletsprojects.com/en/stable/templates/)
- [Jinja inheritance](https://jinja.palletsprojects.com/en/stable/templates/#template-inheritance)

## Offline Execution Contract

Use local templates, capability data, and golden outputs. If a vendor template or renderer is unavailable, generate the vendor-neutral model and an explicit unsupported-capability report rather than copying syntax from another platform.

## Architecture & Technical Design Patterns

Represent platform selection as data, for example:

```yaml
device:
  name: leaf-1
  platform: cisco_iosxe
  version: "17.12"
  capabilities: [lacp, ospf, evpn]
intent:
  interfaces:
    - name: GigabitEthernet1/0/1
      mode: trunk
      vlans: [10, 20]
```

Resolve `platform + major_version + feature` through an allow-listed capability
registry. Keep shared macros for data iteration and vendor templates for CLI
syntax. A missing capability must produce a structured error; a vendor branch
must not silently omit a required feature. Render one device at a time with
`StrictUndefined`, stable sorting, and a golden fixture per supported vendor
and version. Test the same intent against each adapter and compare semantics,
not literal syntax.
