---
name: ansible-vault-hygiene
description: "[Tier: Basic] Secure Ansible network repositories with ansible-vault, vault-variable indirection, and external secret lookups. Use this skill when playbooks, roles, inventories, or logs handle passwords, tokens, keys, SNMP communities, or other credentials."
license: MIT
compatibility: Ansible Core; ansible-vault; optional community.hashi_vault, amazon.aws, or cloud secret providers; CI secret scanning
---

# Ansible Vault Hygiene (Basic)

Make secret handling boring and auditable. The playbook should reference a
secret, not know how to print or persist it.

## Core Engineering Capabilities

- Organize clear variable names that point to encrypted `vault.yml` values.
- Use Vault IDs, external secret lookups, and environment-injected credentials.
- Scan repositories for leaked passwords, keys, tokens, and private material.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never commit plaintext secrets, decrypted vault files, vault passwords, or
  secrets in defaults, examples, fixtures, or CI artifacts.
- Use `no_log: true` on tasks and blocks that handle credentials; understand
  that `no_log` can reduce diagnostics and compensate with sanitized status.
- Keep secret variable names distinct from non-secret configuration and avoid
  exposing them through `debug`, registered output, facts, or failure text.
- Rotate compromised credentials; scanning is not remediation.
- Use least-privilege secret paths and verify external lookup behavior in CI.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Map every secret source, vault ID, variable file, environment variable, log path, and CI context. Identify values that must remain encrypted at rest and values that may be exposed to a target module.

### Phase 2 (Generation)

Generate Vault-backed vars and task usage with no_log at secret boundaries, explicit vault-id handling, and safe failure messages. Keep secret names stable while keeping secret values out of fixtures and rendered output.

### Phase 3 (Self-Verification)

Run the leak scanner against source, logs, diffs, and failed-task output. Test wrong vault IDs, missing secrets, check mode, and accidental debug statements; confirm the scanner catches known canaries without false confidence.

1. Classify secret fields and choose Vault or an approved external provider.
2. Reference `vault_` variables through clear, non-secret role interfaces.
3. Encrypt, scan, syntax-check, and test with injected CI credentials.
4. Review logs and artifacts for redaction before publishing results.

## Production Code / Template Example

### Input / Requirement

Provide the secret inventory, vault layout, CI or controller invocation, redaction requirements, and sanitized canary values for testing.

### Output / Generated Code

Return the encrypted-variable layout, playbook changes, invocation examples, leak-scan results, and a rotation or recovery note.


```yaml
# vars/main.yml
ansible_user: "{{ vault_ansible_user }}"
ansible_password: "{{ vault_ansible_password }}"

# tasks/main.yml
- name: Configure authenticated session
  no_log: true
  ansible.builtin.set_fact:
    session_token: "{{ lookup('env', 'NETOPS_TOKEN') }}"
```

## Validation, Linting & Testing Commands

- Run the bundled secret scanner and `ansible-vault view` only in a secure
  operator context.
- Test missing/expired secrets and ensure errors do not echo values.
- Rotate any secret found by the scanner; do not merely delete the line.
- Run `python3 scripts/validate_skills.py`.

## References

- [Ansible Vault guide](https://docs.ansible.com/projects/ansible/latest/vault_guide/index.html)
- [Ansible no_log](https://docs.ansible.com/projects/ansible/latest/reference_appendices/logging.html)

## Offline Execution Contract

Secret scanning and variable-structure checks work locally. Without Ansible Vault or an external secret provider, use placeholders and test redaction; never substitute plaintext credentials.

## Architecture & Technical Design Patterns

Use a three-layer naming pattern: role interface variables such as
`netops_username`, secret references such as `vault_netops_password`, and the
provider lookup that supplies the secret. Keep `vars/main.yml` non-secret and
load encrypted `vars/vault.yml` explicitly. Use Vault IDs when multiple
environments need separate keys, and inject the vault password through a
credential store or CI secret—not a repository file.

`no_log: true` belongs on tasks that receive, transform, register, or fail with
secrets. Do not put secret-bearing values in `debug`, `assert` messages,
changed output, host facts, or filenames. A scanner finding requires rotation
and repository/history review; deleting the line is not remediation. Test
missing, expired, unauthorized, and provider-timeout cases without echoing the
secret value.
