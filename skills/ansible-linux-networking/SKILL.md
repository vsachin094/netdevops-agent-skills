---
name: ansible-linux-networking
description: "[Tier: Intermediate] Build Ansible roles for Linux server and gateway networking, including sysctl tuning, Netplan/NetworkManager VLANs and bonds, FRRouting, nftables, and WireGuard. Use this skill when Linux networking changes need validation before handlers restart services and must avoid management lockout."
license: MIT
compatibility: Ansible Core 2.15+; Linux systemd; Netplan 0.105+ or NetworkManager 1.40+; FRRouting 8.5+; nftables 1.0+; WireGuard kernel module; target distribution docs (Ubuntu 22.04/24.04, RHEL 9, Debian 12)
---

# Ansible Linux Networking (Intermediate)

Treat a Linux network change as a potential loss-of-access event. Render and validate configuration before restart, retain a recovery path, and never assume the control interface is unaffected by a route or firewall change.

## Core Engineering Capabilities

- Configure sysctl, VLANs, LACP bonds, static routes, Netplan, NetworkManager, FRR (OSPF/BGP/ISIS), nftables, and WireGuard through reusable roles.
- Validate generated configuration with `nft -c -f`, `vtysh -C`, `netplan try`, `nmcli connection verify`, or platform-native check commands before notifying restart handlers.
- Model management-interface protection: detect active SSH path, validate post-change reachability, enforce timed rollback on failure.
- Produce idempotent roles with check-mode support, molecule scenarios, and CI-validated test matrices across Ubuntu, Debian, RHEL/Fedora.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- **Detect the active SSH management path before changing addresses, routes, firewall rules, or bond membership.** Run `ip route get <ansible_host>` and `ss -tnp state established '( sport = :ssh or dport = :ssh )'` to identify the interface and next-hop carrying the control session. Fail the play if the target change touches that path without an explicit override.
- **Validate syntax and semantics before restarting networking, FRR, or firewall services.** Use handlers only after a changed and valid configuration. Never restart a service on a "check" pass.
- **Use distribution-specific task files.** Do not assume NetworkManager, systemd-networkd, or Netplan is installed. Detect with `ansible_facts.services` or `which` and include the correct backend tasks.
- **Keep nftables default-deny policy explicit** with an established/related and management allow-list. Never flush a live firewall without a tested rollback rule set.
- **Make WireGuard keys external and permissions restrictive** (`mode: "0600"`, owned by root). Generate keys in CI or a key ceremony, not in the role.
- **FRR config must pass `vtysh -C` before reload.** A syntax error in `frr.conf` leaves the daemon running with stale config — not a safe state.
- **Netplan `try` is not a substitute for pre-validation.** It rolls back after 120s but leaves the system in an undefined state during that window. Validate with `netplan generate` first.
- **Bond/VLAN changes require parent interface validation.** Verify the intended parent/link exists and is up before creating the VLAN or bond slave.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: target distribution/version, active network backend (`networkmanager` or `systemd-networkd`), interface names, current IP/routes, SSH source IP/interface, existing firewall policy, FRR/nftables/WireGuard service state, maintenance window, and rollback SLA. Reject any request that cannot identify a recovery path for a remote host.

### Phase 2 (Implementation)

1. **Backend detection** — tasks/`detect_backend.yml` sets `linux_network_backend` fact.
2. **Pre-flight** — `assert` that management interface is not in the change set, or that a secondary path exists.
3. **Render candidate config** to `/tmp/<role>-<timestamp>/` using backend-specific templates.
4. **Native validation** — run the platform check command (`nft -c -f`, `vtysh -C`, `netplan generate`, `nmcli connection verify`) on the candidate.
5. **Atomic install** — copy validated candidate to final location, notify handler.
6. **Post-check** — handler runs service restart, then role runs reachability/adjacency/firewall/FRR/WG verification tasks.
7. **Rollback trigger** — any post-check failure fires a rollback handler that restores the previous config and restarts services.

### Phase 3 (Verification)

Run in Molecule with multiple scenarios: `ubuntu22-netplan`, `ubuntu24-netplan`, `debian12-networkmanager`, `rhel9-networkmanager`, `rocky9-networkmanager`. Test: clean install, second run (idempotence), invalid syntax (handler not fired), management interface change (pre-flight blocks), bond/VLAN creation, FRR config with BGP/OSPF, nftables default-deny with allow-list, WireGuard peer add/remove. Exercise rollback by injecting a post-check failure.

## Production Code / Template Example

### Input / Requirement

Provide: target distribution and version, active network backend, interface and route facts, desired network state (interfaces, VLANs, bonds, routes, FRR config, nftables rules, WireGuard peers), SSH management path, recovery constraints (max downtime, rollback SLA).

### Output / Generated Code

Return an idempotent role with: `tasks/main.yml`, backend-specific task files, handlers, templates, `vars/` per distro, `defaults/main.yml`, Molecule scenarios, pre-flight and post-check tasks, rollback handler, and exact native validation commands for the selected distribution.

```yaml
# tasks/preflight.yml
- name: Identify SSH management path
  ansible.builtin.shell: |
    ip route get {{ ansible_host }} | awk '{for(i=1;i<=NF;i++) if($i=="dev") print $(i+1)}'
  register: mgmt_iface
  changed_when: false
  check_mode: false

- name: Fail if management interface is targeted for change
  ansible.builtin.assert:
    that:
      - mgmt_iface.stdout not in linux_network_interfaces_to_change
    fail_msg: "Change targets management interface {{ mgmt_iface.stdout }}. Define a secondary path or set linux_network_allow_mgmt_disrupt: true."
    quiet: true

- name: Capture current configs for rollback
  ansible.builtin.command: "{{ item.cmd }}"
  register: linux_network_backup
  loop:
    - { cmd: "nft list ruleset", dest: "/tmp/net-rollback/nftables.rules" }
    - { cmd: "vtysh -c 'show running-config'", dest: "/tmp/net-rollback/frr.conf" }
    - { cmd: "cat /etc/netplan/*.yaml", dest: "/tmp/net-rollback/netplan.yaml" }
    - { cmd: "nmcli -t -f all connection show", dest: "/tmp/net-rollback/nm-connections.txt" }
  changed_when: false
  check_mode: false
  delegate_to: localhost
  become: true
```

```yaml
# tasks/validate_nftables.yml
- name: Validate nftables candidate
  ansible.builtin.command: nft -c -f {{ linux_network_nftables_candidate }}
  register: nft_validate
  changed_when: false
  failed_when: nft_validate.rc != 0
  check_mode: false

- name: Install validated nftables ruleset
  ansible.builtin.copy:
    src: "{{ linux_network_nftables_candidate }}"
    dest: /etc/nftables.conf
    mode: "0640"
    backup: true
  notify: restart nftables
```

```yaml
# handlers/main.yml
- name: restart nftables
  ansible.builtin.systemd:
    name: nftables
    state: restarted
  listen: "restart nftables"

- name: rollback network config
  ansible.builtin.block:
    - name: Restore nftables
      ansible.builtin.copy:
        src: /tmp/net-rollback/nftables.rules
        dest: /etc/nftables.conf
        mode: "0640"
      notify: restart nftables
    - name: Restore FRR
      ansible.builtin.copy:
        src: /tmp/net-rollback/frr.conf
        dest: /etc/frr/frr.conf
        mode: "0640"
      notify: restart frr
    - name: Restore Netplan
      ansible.builtin.copy:
        src: /tmp/net-rollback/netplan.yaml
        dest: /etc/netplan/01-netcfg.yaml
        mode: "0640"
      notify: netplan apply
    - name: Restore NetworkManager
      ansible.builtin.shell: |
        while read -r line; do
          nmcli connection up "$(echo "$line" | cut -d: -f1)"
        done < /tmp/net-rollback/nm-connections.txt
      notify: restart NetworkManager
  listen: "rollback network config"
```

```jinja2
# templates/nftables.conf.j2
{% set mgmt_iface = linux_network_mgmt_interface %}
{% set mgmt_cidr = linux_network_mgmt_cidr %}
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;
    iifname "lo" accept
    ct state established,related accept
    iifname "{{ mgmt_iface }}" ip saddr {{ mgmt_cidr }} tcp dport 22 accept
    icmp type echo-request limit rate 5/second accept
    counter drop
  }
  chain forward {
    type filter hook forward priority 0; policy drop;
  }
  chain output {
    type filter hook output priority 0; policy accept;
  }
}
```

## Validation, Linting & Testing Commands

- **Syntax and style:** `ansible-lint`, `yamllint .`
- **Molecule test matrix:** `molecule test -s ubuntu22-netplan && molecule test -s ubuntu24-netplan && molecule test -s debian12-nm && molecule test -s rhel9-nm`
- **Native validators:** `nft -c -f /etc/nftables.conf`, `vtysh -C`, `netplan generate`, `nmcli connection verify <name>`
- **Idempotence:** Run playbook twice; second run must show `changed=0` for all tasks.
- **Lockout test:** Target the management interface in a VM; verify pre-flight blocks the change.
- **Rollback test:** Inject a post-check failure (e.g., bad FRR config); verify rollback handler restores previous config and services recover.
- **CI gate:** `python3 scripts/validate_skills.py` from repository root.

## References

- [Ansible handlers](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_handlers.html)
- [nftables wiki](https://wiki.nftables.org/)
- [FRRouting documentation](https://docs.frrouting.org/)
- [Netplan reference](https://netplan.io/reference)
- [NetworkManager CLI](https://developer-old.gnome.org/NetworkManager/stable/nmcli.html)

## Offline Execution Contract

Render and validate candidate Linux configs against local fixture commands or containers. Without a target host, do not claim route, firewall, FRR, WireGuard, or management reachability success. Molecule with `delegated` driver against local VMs/containers is the minimum validation.

## Architecture & Technical Design Patterns

Gather `ansible_distribution`, `ansible_distribution_version`, network facts, default route, SSH source/path, active connection manager, and service state before changing anything. Select one backend — Netplan/networkd or NetworkManager — and fail if the requested backend is absent. Render to a temporary path, validate with native tool, install atomically, then notify a handler.

**Validation commands per backend:**
- nftables: `nft -c -f <candidate>`
- FRR: `vtysh -C -f <candidate>` (or `vtysh -c "configure terminal" -c "load <candidate>"` for partial)
- Netplan: `netplan generate` (dry-run), `netplan try --timeout 30` (with timeout)
- NetworkManager: `nmcli connection verify <connection-name>`
- systemd-networkd: `networkctl reload` (validates .network files)

**Management protection pattern:**
```yaml
- name: Verify post-change reachability
  ansible.builtin.wait_for:
    host: "{{ ansible_host }}"
    port: 22
    timeout: 30
    state: started
  delegate_to: localhost
  become: false
  ignore_errors: true
  register: ssh_check

- name: Trigger rollback on reachability loss
  ansible.builtin.meta: flush_handlers
  when: ssh_check.failed
  notify: rollback network config
```

**FRR config generation:** Use `frr.conf.j2` with structured data (not raw CLI lines). Validate each protocol section (OSPF, BGP, ISIS) independently before assembling. BGP peers must have explicit `update-source`, `password` (reference only), `ebgp-multihop` where needed, and `bfd` profile.

**WireGuard:** Keys via `ansible.builtin.slurp` from a secrets path or `lookup('env', 'WG_PRIVATE_KEY')`. Never generate in-role. `PostUp`/`PostDown` scripts for routing adjustments must be idempotent and tested.

**Bond/LACP:** Require `mii-monitor-interval: 100` and `mode: 802.3ad` with `lacp-rate: fast` for sub-second failover. Validate peer switch config matches before applying.

## Vendor Version Compatibility

| Distribution | Version | Netplan | NetworkManager | systemd-networkd | FRR | nftables | WireGuard |
|--------------|---------|---------|----------------|------------------|-----|----------|-----------|
| Ubuntu       | 22.04   | 0.105   | 1.36           | 249              | 8.1 | 1.0      | 5.15      |
| Ubuntu       | 24.04   | 0.107   | 1.44           | 255              | 8.5 | 1.0      | 6.8       |
| Debian       | 12      | 0.106   | 1.36           | 252              | 8.5 | 1.0      | 6.1       |
| RHEL/Rocky   | 9       | N/A     | 1.42           | 252              | 8.4 | 1.0      | 5.14      |
| Fedora       | 39      | 0.107   | 1.44           | 254              | 8.5 | 1.1      | 6.5       |

**Notes:**
- Ubuntu 22.04+ uses Netplan by default; NetworkManager available for desktop
- RHEL 9 uses NetworkManager exclusively; Netplan not supported
- FRR 8.5+ required for `vtysh -C` config validation
- WireGuard kernel module required (built-in 5.6+)

## Related Skills

- [netmiko-core](netmiko-core.md) — SSH transport for device push when Ansible connection fails
- [containerlab-topologies](containerlab-topologies.md) — Lab validation for Linux network configs
- [ansible-vault-hygiene](ansible-vault-hygiene.md) — Secure WireGuard key management
- [network-change-runbooks](network-change-runbooks.md) — Pre/post checks for Linux network changes
- [config-diff-audit](config-diff-audit.md) — Drift detection for managed Linux hosts