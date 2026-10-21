---
name: ansible-dynamic-inventory
description: "[Tier: Intermediate] Build Ansible inventory plugin configurations for NetBox, Nautobot, AWS, Azure, and Terraform sources with keyed groups, compose variables, status filters, and caching. Use this skill when inventory changes over time and static hosts files cannot remain authoritative."
license: MIT
compatibility: Ansible Core; relevant vendor/cloud collections; source API credentials; optional persistent inventory cache
---

# Ansible Dynamic Inventory (Intermediate)

Make the source-of-truth query explicit and reproducible. Dynamic inventory
should classify reachable, active objects and produce stable host variables
without embedding secrets or stale assumptions.

## Core Engineering Capabilities

- Configure inventory plugins for NetBox/Nautobot, AWS EC2, Azure, and
  Terraform/OpenTofu handoffs.
- Use `keyed_groups`, `compose`, filters, host naming, and persistent caching.
- Validate inventory output and expose source/API failures clearly.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Prefer inventory plugins over legacy scripts and static `hosts.ini` for a
  dynamic source.
- Filter lifecycle status explicitly, such as `active`, and avoid targeting
  decommissioned or unmanaged objects.
- Use stable host keys, deterministic groups, and documented precedence when
  multiple sources provide the same variable.
- Keep API tokens external and make cache hits optional; stale or missing cache
  must not silently become a production inventory.
- Use `keyed_groups` and `compose` for classification, not arbitrary shell
  commands or `local-exec` side effects.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define authoritative source, filters, host key, groups, variables, and TTL.
2. Configure plugin and credentials securely.
3. Run `ansible-inventory --graph --vars` against a lab/source snapshot.
4. Test source outage, empty result, duplicate host, stale cache, and status
   changes before enabling deployment jobs.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```yaml
plugin: netbox.netbox.nb_inventory
api_endpoint: "{{ lookup('env', 'NETBOX_URL') }}"
token: "{{ lookup('env', 'NETBOX_TOKEN') }}"
validate_certs: true
device_query_filters:
  status: active
keyed_groups:
  - prefix: site
    key: site.slug
compose:
  ansible_host: primary_ip4.address | ipaddr('address')
```

## Validation, Linting & Testing Commands

- Run `ansible-inventory --list` and `--graph`; assert expected active hosts
  and groups.
- Test API auth failure, outage, duplicate names, missing primary IP, and
  stale cache behavior.
- Run `python3 scripts/validate_skills.py`.

## References

- [Dynamic inventory guide](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_dynamic_inventory.html)
- [Inventory cache plugins](https://docs.ansible.com/projects/ansible/latest/plugins/cache.html)
- [AWS keyed groups example](https://docs.ansible.com/projects/ansible/latest/collections/amazon/aws/docsite/aws_ec2_guide.html)

## Offline Execution Contract

Use saved API responses and inventory fixtures to test filters, groups, compose values, and cache behavior. Without the source API, never fabricate hosts; return an empty or dependency-blocked inventory with a clear reason.

## Architecture & Technical Design Patterns

An inventory plugin configuration has four separate concerns: source/auth,
selection filters, host identity, and grouping/composition. Select lifecycle
status before grouping; select a stable host key such as device name or cloud
instance ID; then compose `ansible_host`, `ansible_network_os`, site, role,
platform, and credential references. `keyed_groups` creates group names from
host variables and must use sanitized values. `compose` should not contain
side-effecting commands.

Run `ansible-inventory --list`, `--graph`, and `--host <name>` in CI and assert
expected host count, groups, addresses, and no secret-valued variables. Cache
is an optimization, not authority: include TTL/source metadata, fail or warn
on stale cache according to environment policy, and never use a stale cache to
deploy when the API is unreachable unless explicitly approved.
