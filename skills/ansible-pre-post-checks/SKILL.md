---
name: ansible-pre-post-checks
description: "Wrap Ansible network changes in structured pre-change snapshots, controlled execution, post-change assertions, and rescue rollback. Use this skill when a change must prove BGP, OSPF, interface, or service health remains within an approved baseline."
license: MIT
compatibility: Ansible Core; vendor network collections; cli_parse or structured facts; Huawei VRP display output via bundled normalizer; optional NAPALM/pyATS/Containerlab
---

# Ansible Pre/Post Checks (Advanced)

Make operational safety a playbook stage rather than an operator memory item. The baseline must be comparable, the change bounded, and rollback explicit.

## Core Engineering Capabilities

- Capture structured pre-change state, execute a change, and compare post-state.
- Assert BGP established counts, OSPF neighbors, interface state, reachability, and service-specific invariants.
- Use `block`, `rescue`, and `always` to rollback and report cleanup results.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Normalize snapshots and exclude documented volatile fields; never compare raw command text when order or counters are unstable.
- Scope assertions to the intended device, VRF, address family, and peer set. A global count can mask a failed critical neighbor.
- Fail closed when the baseline is incomplete or parser output is malformed.
- Make rescue rollback idempotent and verify it; `rescue` is not proof that the device returned to baseline.
- Always emit baseline, postcheck, failure, and rollback artifacts without exposing secrets.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Define the pre-change facts, the exact change boundary, post-change assertions, acceptable transient states, and rollback trigger. Identify which checks are safe to run against the target and which require a lab fixture.

### Phase 2 (Implementation)

Build a block/rescue workflow that snapshots state, performs the change, evaluates explicit postconditions, and restores the approved snapshot on failure. Keep rescue logic bounded and observable rather than hiding errors.

### Phase 3 (Verification)

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
- name: Network change with pre/post checks
  hosts: network
  gather_facts: false
  tasks:
    - block:
        - name: Capture baseline
          cisco.ios.ios_facts:
            gather_network_resources: [bgp_global, ospf_interfaces]
          register: before
          changed_when: false

        - name: Apply change
          cisco.ios.ios_config:
            lines:
              - "router bgp 65001"
              - "neighbor 192.0.2.1 description managed"
          register: change

      rescue:
        - name: Roll back approved commands
          cisco.ios.ios_config:
            lines:
              - "router bgp 65001"
              - "no neighbor 192.0.2.1 description managed"
          register: rollback

      always:
        - name: Collect final evidence
          cisco.ios.ios_command:
            commands: [show ip bgp summary]
          register: after
          changed_when: false

        - name: Assert BGP peers unchanged
          assert:
            that:
              - "after.stdout[0] | regex_search('Estab') == before.stdout[0] | regex_search('Estab')"
            fail_msg: "BGP peer count changed"
```

```python
# scripts/normalize_bgp.py
import re
def normalize_bgp(output: str) -> dict:
    peers = {}
    for line in output.splitlines():
        m = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+\d+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+(\w+)', line)
        if m:
            peers[m.group(1)] = m.group(2)
    return peers
```

### Huawei VRP Variant

VRP has no resource modules for BGP or interface state in this workflow, so capture `display` output as text, normalize it with `scripts/normalize_vrp.py`, and assert on the normalized data. The normalizer covers `display bgp peer` (IPv4 peers), `display ospf peer brief` (OSPFv2, keyed per process, area, interface and neighbor) and `display interface brief`, drops volatile fields (message counters, OutQ, Up/Down timers, utilization, error counters), and fails closed when the header is missing, a row does not match the documented layout, or the parsed peer count differs from the device's `Total number of peers` (BGP) or per-process `Total Peer(s)` (OSPF) line.

Transport is deployment-specific. The example uses `ansible.netcommon` with `ansible_network_os: community.network.ce`; that collection was removed from the Ansible 12 package and its repository is archived, so install it explicitly and pin it, or substitute the transport your environment supports. The `ce` plugins target CloudEngine; behavior on other VRP platforms is not verified here. VRP command syntax and two-stage commit behavior also differ between releases, so the change and rollback lines below are illustrative.

```yaml
- name: VRP change with pre/post checks
  hosts: vrp
  gather_facts: false
  vars:
    ansible_connection: ansible.netcommon.network_cli
    ansible_network_os: community.network.ce   # see transport note above
    evidence_dir: "evidence/{{ inventory_hostname }}"
    normalizer: "{{ playbook_dir }}/scripts/normalize_vrp.py"
  tasks:
    - name: Prepare evidence directory
      ansible.builtin.file:
        path: "{{ evidence_dir }}"
        state: directory
        mode: "0750"
      delegate_to: localhost

    - name: Capture baseline
      ansible.netcommon.cli_command:
        command: "{{ item }}"
      loop: [display bgp peer, display ospf peer brief, display interface brief]
      register: baseline_raw
      changed_when: false

    - name: Save baseline evidence
      ansible.builtin.copy:
        content: "{{ item.stdout }}"
        dest: "{{ evidence_dir }}/{{ item.item | replace(' ', '_') }}.baseline.txt"
        mode: "0640"
      loop: "{{ baseline_raw.results }}"
      delegate_to: localhost

    - name: Validate baseline parses (fails closed)
      ansible.builtin.command: >-
        python3 {{ normalizer }} {{ item.kind }}
        {{ evidence_dir }}/{{ item.file }}.baseline.txt
      loop:
        - {kind: bgp-peer, file: display_bgp_peer}
        - {kind: ospf-peer-brief, file: display_ospf_peer_brief}
        - {kind: interface-brief, file: display_interface_brief}
      changed_when: false
      delegate_to: localhost

    - block:
        - name: Apply change
          ansible.netcommon.cli_config:
            config: |
              bgp 65001
               peer 192.0.2.1 description managed
          register: change

        - name: Capture postcheck
          ansible.netcommon.cli_command:
            command: "{{ item }}"
          loop: [display bgp peer, display ospf peer brief, display interface brief]
          register: post_raw
          changed_when: false

        - name: Save postcheck evidence
          ansible.builtin.copy:
            content: "{{ item.stdout }}"
            dest: "{{ evidence_dir }}/{{ item.item | replace(' ', '_') }}.post.txt"
            mode: "0640"
          loop: "{{ post_raw.results }}"
          delegate_to: localhost

        - name: Assert no BGP peer, OSPF adjacency or interface regressed
          ansible.builtin.command: >-
            python3 {{ normalizer }} compare {{ item.kind }}
            {{ evidence_dir }}/{{ item.file }}.baseline.txt
            {{ evidence_dir }}/{{ item.file }}.post.txt
          loop:
            - {kind: bgp-peer, file: display_bgp_peer}
            - {kind: ospf-peer-brief, file: display_ospf_peer_brief}
            - {kind: interface-brief, file: display_interface_brief}
          changed_when: false
          delegate_to: localhost

      rescue:
        - name: Roll back approved commands
          ansible.netcommon.cli_config:
            config: |
              bgp 65001
               undo peer 192.0.2.1 description
          register: rollback

        - name: Report rollback outcome
          ansible.builtin.fail:
            msg: "Change rolled back on {{ inventory_hostname }}; rerun the postcheck to classify recovered / not_recovered / unknown"

      always:
        - name: Collect final evidence
          ansible.netcommon.cli_command:
            command: display bgp peer
          register: final_bgp
          changed_when: false
```

The compare step exits 1 when any peer that was `Established` in the baseline is missing, changes remote AS, or leaves `Established`; when any OSPF adjacency that was `Full` is missing or no longer `Full` (a `2-Way` adjacency, normal between DROther routers, must stay `2-Way` or `Full`); and when any interface that was `up`/`up` is missing or no longer `up`/`up`. Administratively down interfaces (`*down`) in the baseline are not treated as regressions. Exit code 2 means the output could not be parsed and the run must stop. Sanitized fixtures for these cases live in `fixtures/vrp/`.

## Validation, Linting & Testing Commands

- Test failed baseline, change failure, postcheck failure, rescue failure, and successful idempotent repeat.
- Assert critical neighbor identities, not only aggregate totals.
- Run `ansible-lint`, lab tests, and `python3 scripts/validate_skills.py`.
- For the VRP variant, run `python3 skills/ansible-pre-post-checks/scripts/test_normalize_vrp.py` from the repository root; it uses only the offline fixtures and the Python standard library.

## References

- [Ansible blocks and error handling](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_blocks.html)
- [Ansible assert module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/assert_module.html)
- [Huawei AR V200R010 — Example for Configuring Basic BGP Functions (`display bgp peer` output)](https://support.huawei.com/enterprise/en/doc/EDOC1100034072/9a2ddc78/example-for-configuring-basic-bgp-functions)
- [Huawei S1720/S2700/S5700/S6720 V200R011C10 — BGP Configuration Commands (peer State values)](https://support.huawei.com/enterprise/en/doc/EDOC1000178165/54c86941/bgp-configuration-commands)
- [Huawei WLAN AC V200R019C00 Command Reference — `display ospf peer` (brief output and neighbor State values)](https://support.huawei.com/enterprise/en/doc/EDOC1100096312/9dc18ce0/display-ospf-peer)
- [Huawei S1720/S2700/S5700/S6720 V200R011C10 — Basic Interface Configuration Commands (`display interface brief` fields)](https://support.huawei.com/enterprise/en/doc/EDOC1000178165/cdd85713/basic-interface-configuration-commands)
- [community.network collection (removed from Ansible 12)](https://docs.ansible.com/projects/ansible/latest/collections/community/network/index.html)

## Offline Execution Contract

Use saved baseline/postcheck fixtures to test assertions and rescue logic. For Huawei VRP, `fixtures/vrp/` holds sanitized `display` outputs (RFC 5737 addresses, private ASNs) covering a clean postcheck, a named BGP peer regression, OSPF adjacency regressions, an interface regression, and truncated output that must fail closed. Without devices, validate comparison semantics and rollback commands as artifacts only; never claim operational recovery.

## Architecture & Technical Design Patterns

Represent a baseline as structured data, not raw text:

```yaml
bgp:
  ipv4_unicast: {established: 4, peers: [192.0.2.1, 192.0.2.2]}
interfaces:
  GigabitEthernet0/0: {admin: up, oper: up}
```

Capture the same fields after the change. Assert critical peer identity and state, not only an aggregate count; permit an explicitly documented delta such as one new peer while requiring all existing peers to remain established. Put the change and postcheck in a `block`, rollback in `rescue`, and evidence collection in `always`. If rollback runs, perform the same postcheck against the baseline and report `recovered`, `not_recovered`, or `unknown` separately. Do not use `ignore_errors` to continue after a missing baseline or malformed parser result.