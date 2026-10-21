---
name: ansible-role-scaffolding
description: "[Tier: Intermediate] Scaffold reusable multi-vendor Ansible roles with defaults, tasks, handlers, templates, argument specs, Molecule scenarios, and documentation. Use this skill when a network automation workflow must become a validated, versioned role with check-mode support."
license: MIT
compatibility: Ansible Core; ansible-lint; Molecule; vendor collections; YAML; optional Docker/Podman lab
---

# Ansible Role Scaffolding (Intermediate)

A role is a public interface. Treat defaults, argument specs, supported
platforms, idempotency, and check mode as API commitments.

## Core Engineering Capabilities

- Create role layout: `defaults/`, `vars/`, `tasks/`, `handlers/`, `templates/`,
  `meta/argument_specs.yml`, `molecule/`, and README.
- Split vendor tasks by OS, expose typed inputs, and test convergence and
  failure paths with Molecule.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Validate inputs with `meta/argument_specs.yml`; document defaults and
  supported platforms.
- Keep secrets out of defaults and examples, use FQCNs, and honor check mode.
- Separate `tasks/ios.yml`, `tasks/nxos.yml`, and `tasks/eos.yml`; fail clearly
  for unsupported network OS rather than choosing a nearby syntax.
- Use handlers only for necessary reload/restart actions and validate rendered
  configuration before invoking them.
- Target clean `ansible-lint` production profile and deterministic Molecule
  scenarios.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define role contract and supported OS matrix.
2. Scaffold layout and argument specs, then implement vendor task includes.
3. Add idempotent converge, check-mode, invalid-input, and platform tests.
4. Run lint, syntax, Molecule, and documentation checks before release.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```yaml
# meta/argument_specs.yml
argument_specs:
  main:
    options:
      netops_interfaces:
        type: list
        elements: dict
        required: true
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Run `ansible-lint`, `ansible-playbook --syntax-check`, and Molecule.
- Verify second converge produces no changes and unsupported OS fails safely.
- Run `sh skills/ansible-role-scaffolding/scripts/run_ansible_lint.sh`.

## References

- [Ansible role guide](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html)
- [Ansible argument specs](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html#role-argument-validation)

## Offline Execution Contract

Role layout, argument specs, YAML, and unit fixtures can be authored offline. Without Ansible/Molecule, validate structure and document the exact later commands required for lint and convergence testing.

## Architecture & Technical Design Patterns

Use this layout:

```text
defaults/main.yml  vars/main.yml  tasks/main.yml  tasks/ios.yml
tasks/nxos.yml     handlers/main.yml  templates/  meta/argument_specs.yml
molecule/default/{converge,verify,molecule}.yml  README.md
```

`tasks/main.yml` validates arguments, asserts supported `ansible_network_os`,
and includes the vendor task file. Defaults are safe and non-secret; vars are
for implementation constants; user intent belongs in role parameters. Argument
specs must define type, required/default, choices, elements, and sensitive
behavior where relevant. Every handler must be notified only after a changed
and validated template/resource. Molecule should test first converge, second
converge with no changes, check mode, invalid input, and unsupported platform.
