---
name: ansible-linux-networking
description: "[Tier: Intermediate] Build Ansible roles for Linux server and gateway networking, including sysctl tuning, Netplan/NetworkManager VLANs and bonds, FRRouting, nftables, and WireGuard. Use this skill when Linux networking changes need validation before handlers restart services and must avoid management lockout."
license: MIT
compatibility: Ansible Core; Linux systemd; Netplan or NetworkManager; FRRouting; nftables; WireGuard; target distribution documentation
---

# Ansible Linux Networking (Intermediate)

Treat a Linux network change as a potential loss-of-access event. Render and
validate configuration before restart, retain a recovery path, and never
assume the control interface is unaffected by a route or firewall change.

## Core Engineering Capabilities

- Configure sysctl, VLANs, LACP bonds, routes, Netplan, NetworkManager, FRR,
  nftables, and WireGuard through reusable roles.
- Validate generated configuration with `nft -c -f`, `vtysh -C`, Netplan
  try/generate, or the platform's native check command before handlers.
- Model management-interface protection and explicit rollback/recovery.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Detect the active SSH management path before changing addresses, routes,
  firewall rules, or bond membership; fail rather than risking lockout.
- Validate syntax and semantics before restarting networking, FRR, or firewall
  services. Use handlers only after a changed and valid configuration.
- Use distribution-specific task files and avoid assuming NetworkManager,
  systemd-networkd, or Netplan is installed.
- Keep nftables default-deny policy explicit with an established/related and
  management allow-list; never flush a live firewall without recovery.
- Make WireGuard keys external and permissions restrictive.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Collect the distribution, network manager, interface names, default route, SSH source path, existing firewall policy, and service state before changing anything. Reject a request that does not identify a recovery path for a remote host.

### Phase 2 (Generation)

Select the installed backend—Netplan/networkd or NetworkManager—and generate distribution-specific tasks for routes, VLANs, bonds, FRR, nftables, or WireGuard. Render and validate temporary configuration before notifying a restart handler.

### Phase 3 (Self-Verification)

Run native syntax checks, apply the change in a VM or namespace lab, and assert the management route, interface state, firewall policy, FRR neighbors, and WireGuard handshake. Exercise the rollback path with an intentionally invalid candidate.

1. Gather OS, interface, route, SSH, and service facts.
2. Render candidate config and run native validators.
3. Apply with a controlled handler and a connection/reachability check.
4. Assert routes, neighbors, firewall rules, and service state; rescue with a
   known-good configuration when the postcheck fails.

## Production Code / Template Example

### Input / Requirement

Provide the target distribution and version, active network backend, interface and route facts, desired network state, SSH path, and recovery constraints.

### Output / Generated Code

Return an idempotent role or task set with handlers, prechecks, postchecks, and rollback notes. Include the exact native validation commands for the selected distribution.


```yaml
- name: Validate nftables before install
  ansible.builtin.command: nft -c -f {{ nftables_candidate }}
  changed_when: false
  check_mode: false
```

## Validation, Linting & Testing Commands

- Test clean install, second run, distro variants, invalid syntax, lost route,
  SSH management protection, and handler failure.
- Use a VM/network namespace lab before applying to a gateway.
- Run `ansible-lint`, Molecule, and `python3 scripts/validate_skills.py`.

## References

- [Ansible handlers](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_handlers.html)
- [nftables wiki](https://wiki.nftables.org/)
- [FRRouting documentation](https://docs.frrouting.org/)

## Offline Execution Contract

Render and validate candidate Linux configs against local fixture commands or containers. Without a target host, do not claim route, firewall, FRR, WireGuard, or management reachability success.

## Architecture & Technical Design Patterns

Gather `ansible_distribution`, network facts, default route, SSH source/path,
active connection manager, and service state before changing anything. Select
one backend—Netplan/networkd or NetworkManager—and fail if the requested
backend is absent. Render to a temporary path, validate, install atomically,
then notify a handler. For `nftables`, use `nft -c -f`; for FRR use `vtysh -C`
or the installed daemon check; for Netplan use `netplan generate/try` where
available.

Protect the management route and SSH source interface explicitly. For a bond or
VLAN change, verify the intended parent/link exists and the new address is not
the only path to the control node. Use a timed rollback/revert mechanism for
remote changes, then assert `ip route`, `ip addr`, `nft list ruleset`, FRR
neighbor state, and WireGuard handshake/route state. Never flush a live
firewall as a shortcut to convergence.
