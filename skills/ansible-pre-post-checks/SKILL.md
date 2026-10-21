---
name: ansible-pre-post-checks
description: "[Tier: Advanced] Wrap Ansible network changes in structured pre-change snapshots, controlled execution, post-change assertions, and rescue rollback. Use this skill when a change must prove BGP, OSPF, interface, or service health remains within an approved baseline."
license: MIT
compatibility: Ansible Core; vendor network collections; cli_parse or structured facts; optional NAPALM/pyATS/Containerlab
---

# Ansible Pre/Post Checks (Advanced)

Make operational safety a playbook stage rather than an operator memory item.
The baseline must be comparable, the change bounded, and rollback explicit.

## Core Engineering Capabilities

- Capture structured pre-change state, execute a change, and compare post-state.
- Assert BGP established counts, OSPF neighbors, interface state, reachability,
  and service-specific invariants.
- Use `block`, `rescue`, and `always` to rollback and report cleanup results.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Normalize snapshots and exclude documented volatile fields; never compare
  raw command text when order or counters are unstable.
- Scope assertions to the intended device, VRF, address family, and peer set.
  A global count can mask a failed critical neighbor.
- Fail closed when the baseline is incomplete or parser output is malformed.
- Make rescue rollback idempotent and verify it; `rescue` is not proof that
  the device returned to baseline.
- Always emit baseline, postcheck, failure, and rollback artifacts without
  exposing secrets.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Define the pre-change facts, the exact change boundary, post-change assertions, acceptable transient states, and rollback trigger. Identify which checks are safe to run against the target and which require a lab fixture.

### Phase 2 (Generation)

Build a block/rescue workflow that snapshots state, performs the change, evaluates explicit postconditions, and restores the approved snapshot on failure. Keep rescue logic bounded and observable rather than hiding errors.

### Phase 3 (Self-Verification)

Run the workflow in check mode and a lab, then force failures at the change, postcheck, and rollback stages. Confirm that the original evidence is retained and that a partial fleet result is reported per host.

1. Gather and validate baseline; stop if required signals are missing.
2. Apply the authorized change inside a block.
3. Gather post-state and assert intended and safety invariants.
4. Rescue with rollback, verify recovery, and always publish an outcome.

## Production Code / Template Example

### Input / Requirement

Provide precheck commands, the change play or role, postconditions, rollback artifact, timeout policy, and the definition of a successful run.

### Output / Generated Code

Return the playbook with block/rescue structure, evidence paths, failure injection tests, and an operator runbook for aborting or recovering the change.


```yaml
- block:
    - name: Capture baseline
      cisco.ios.ios_facts:
        gather_network_resources: [bgp_global, ospf_interfaces]
      register: before
      changed_when: false
    - name: Apply change
      cisco.ios.ios_config:
        lines: ["router bgp 65001", "neighbor 192.0.2.1 description managed"]
  rescue:
    - name: Roll back approved commands
      cisco.ios.ios_config:
        lines: ["router bgp 65001", "no neighbor 192.0.2.1 description managed"]
  always:
    - name: Collect final evidence
      cisco.ios.ios_command:
        commands: [show ip bgp summary]
      changed_when: false
```

## Validation, Linting & Testing Commands

- Test failed baseline, change failure, postcheck failure, rescue failure, and
  successful idempotent repeat.
- Assert critical neighbor identities, not only aggregate totals.
- Run `ansible-lint`, lab tests, and `python3 scripts/validate_skills.py`.

## References

- [Ansible blocks and error handling](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_blocks.html)
- [Ansible assert module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/assert_module.html)

## Offline Execution Contract

Use saved baseline/postcheck fixtures to test assertions and rescue logic. Without devices, validate comparison semantics and rollback commands as artifacts only; never claim operational recovery.

## Architecture & Technical Design Patterns

Represent a baseline as structured data, not raw text:

```yaml
bgp:
  ipv4_unicast: {established: 4, peers: [192.0.2.1, 192.0.2.2]}
interfaces:
  GigabitEthernet0/0: {admin: up, oper: up}
```

Capture the same fields after the change. Assert critical peer identity and
state, not only an aggregate count; permit an explicitly documented delta such
as one new peer while requiring all existing peers to remain established.
Put the change and postcheck in a `block`, rollback in `rescue`, and evidence
collection in `always`. If rollback runs, perform the same postcheck against
the baseline and report `recovered`, `not_recovered`, or `unknown` separately.
Do not use `ignore_errors` to continue after a missing baseline or malformed
parser result.
