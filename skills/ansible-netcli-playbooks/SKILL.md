---
name: ansible-netcli-playbooks
description: "[Tier: Basic] Write foundational Ansible network playbooks for facts, read-only commands, and configuration backups using FQCNs and ansible.netcommon.network_cli. Use this skill when automating basic operational collection or safe backup workflows across network devices."
license: MIT
compatibility: Ansible Core; ansible.netcommon; vendor collections such as cisco.ios, arista.eos, cisco.nxos, and junipernetworks.junos
---

# Ansible Network CLI Playbooks (Basic)

Use Ansible's network connection model and fully qualified module names. Keep
read-only collection visibly read-only and make connection, timeout, and
privilege behavior explicit in inventory or group variables.

## Core Engineering Capabilities

- Gather vendor facts, execute operational commands, and back up running
  configuration with network collections.
- Define FQCN-based tasks, network CLI connection variables, privilege
  escalation, timeouts, and structured registered results.
- Produce check-mode-friendly playbooks with explicit `changed_when` behavior.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use `ansible.netcommon.network_cli`; do not use deprecated `connection: local`
  patterns for network modules.
- Use FQCNs such as `cisco.ios.ios_command` and `cisco.ios.ios_facts`.
- Mark read-only commands `changed_when: false`; do not suppress command errors.
- Keep credentials in Ansible Vault or external secret systems and set
  `no_log: true` on secret-handling tasks.
- Set connection and command timeouts appropriate to device latency and never
  hide failed hosts with `ignore_errors` without a reporting plan.
- Write backups atomically with restrictive permissions and sanitize sensitive
  config before sharing.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Identify the network OS, collection and connection plugin, inventory variables, fact requirements, command set, backup location, and whether the task is read-only or mutating. Separate show-command collection from configuration change.

### Phase 2 (Generation)

Generate FQCN-based tasks with explicit timeouts, privilege behavior, redacted output, check-mode handling, and a predictable backup path. Use resource modules where a supported declarative module exists instead of raw command mutation.

### Phase 3 (Self-Verification)

Run ansible-lint, syntax checks, check mode, and fixture-backed parsing. Verify idempotency on a second run and test unreachable devices, privilege failure, malformed output, and backup write failure.

1. Validate inventory, collection versions, and connection variables.
2. Run facts/commands with a bounded timeout and register results.
3. Back up validated running config and emit per-host success/failure.
4. Test with `--check`, `--diff`, and a lab inventory before production.

## Production Code / Template Example

### Input / Requirement

Provide the platform, connection method, inventory variables, commands or desired resource state, backup policy, and the expected evidence after execution.

### Output / Generated Code

Return the playbook, inventory example with secrets omitted, backup and logging behavior, and the commands used for lint, check mode, and test execution.


```yaml
- name: Collect interface state
  hosts: network
  gather_facts: false
  tasks:
    - name: Show interfaces
      cisco.ios.ios_command:
        commands: [show ip interface brief]
      register: interfaces
      changed_when: false
```

## Validation, Linting & Testing Commands

- Run `ansible-lint`, `ansible-playbook --syntax-check`, and a lab execution.
- Test unreachable, authentication, privilege, timeout, and command-error
  paths; ensure the play summary remains accurate.
- Run `python3 scripts/validate_skills.py`.

## References

- [Ansible network connection options](https://docs.ansible.com/projects/ansible/latest/network/getting_started/network_connection_options.html)
- [Ansible network first playbook](https://docs.ansible.com/projects/ansible/latest/network/getting_started/first_playbook.html)

## Offline Execution Contract

Use local Ansible syntax checks, mocked module results, and sanitized fixtures. Without Ansible collections or devices, generate valid playbooks but do not claim FQCN availability or device execution.

## Architecture & Technical Design Patterns

Network inventory should normally define `ansible_connection:
ansible.netcommon.network_cli`, `ansible_network_os`, `ansible_user`, and a
credential reference. Use `gather_facts: false` for network plays and gather
only the required vendor resources. Read-only tasks should register output and
set `changed_when: false`; a backup task should validate that the returned text
is a config, then write it with a host-specific filename and restrictive mode.

Use `ansible_command_timeout`, `ansible_connect_timeout`, and collection-level
timeouts deliberately. Do not use `ignore_errors` to hide unreachable devices;
use `block/rescue`, `failed_when`, and a final summary. Prefer resource modules
for configuration, and use `ios_config`/equivalents only when the desired
operation has no resource-module representation.
