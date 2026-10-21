---
name: ansible-resource-modules
description: "[Tier: Intermediate] Write idempotent Ansible network playbooks with modern resource modules for interfaces, VLANs, BGP, and L3 services. Use this skill when a supported resource module can express the desired state more safely than raw CLI configuration."
license: MIT
compatibility: Ansible Core; ansible.netcommon; vendor network collections and resource modules
---

# Ansible Resource Modules (Intermediate)

Use resource modules as structured reconciliation primitives. The selected
state is part of the change design and must match the intended ownership
boundary.

## Core Engineering Capabilities

- Configure Cisco IOS/NX-OS, Arista EOS, Junos, and other supported resources
  with `merged`, `replaced`, `overridden`, `deleted`, `gathered`, `rendered`,
  and `parsed` states.
- Gather structured device state, render offline configuration, and assert
  before/after idempotency.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Prefer resource modules over legacy `ios_config`, `nxos_config`, `eos_config`,
  and raw `cli_config` when an equivalent resource module exists.
- Choose state deliberately: `merged` adds intent, `replaced` owns a resource
  subsection, and `overridden` can remove unrelated configuration and lock out
  management. Use `overridden` only with explicit ownership and review.
- Pin collection versions and confirm module/platform support.
- Use gathered data and `--check --diff` before change; do not assume check
  mode perfectly models every platform.
- Keep structured config in vars or templates, not embedded opaque CLI.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Identify resource ownership and current state.
2. Gather/parse state, select state mode, and render or diff offline.
3. Apply in a lab, assert idempotency, then run pre/post checks in production.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```yaml
- name: Merge a loopback address
  cisco.ios.ios_l3_interfaces:
    config:
      - name: Loopback100
        ipv4:
          - address: 192.0.2.10/32
    state: merged
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Test every state used, empty config, round-trip, and second-run unchanged
  behavior.
- Review `before`, `after`, and `commands`; assert `changed: false` on repeat.
- Run `ansible-lint`, syntax check, and the repository validator.

## References

- [Ansible network resource modules](https://docs.ansible.com/projects/ansible/latest/network/user_guide/network_resource_modules.html)
- [Resource module development/testing](https://docs.ansible.com/projects/ansible/latest/network/dev_guide/developing_resource_modules_network.html)

## Offline Execution Contract

Use rendered/parsed states and fixture-based before/after data without a device. If the collection is unavailable, retain the FQCN/state contract and mark module availability and device semantics unverified.

## Architecture & Technical Design Patterns

Choose state from ownership: `merged` adds specified elements and preserves
unmanaged peers; `replaced` owns the selected resource subsection; `overridden`
owns the entire resource and can remove unrelated configuration; `deleted`
removes the selected resource; `gathered` returns structured device state;
`rendered` produces native commands offline; `parsed` converts supplied
`running_config` offline. Use `overridden` only when the role is authoritative
for the entire resource, never for a management interface by accident.

The normal lifecycle is gather/inspect, render or check-mode diff, apply,
assert `after`, and run the same task again expecting `changed: false`. Test
empty config, duplicate list keys, unsupported fields, platform version
differences, and the exact `before/commands/after` result. Treat module
warnings and partial failures as review data rather than suppressing them.
