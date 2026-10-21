---
name: ansible-vault-hygiene
description: "[Tier: Intermediate] Secure Ansible network repositories with ansible-vault, vault-id rotation, CI secret scanning, no_log boundaries, and external secret lookups. Use this skill when playbooks, roles, inventories, or logs handle passwords, tokens, keys, SNMP communities, or other credentials and must pass audit."
license: MIT
compatibility: Ansible Core 2.15+; ansible-vault; optional community.hashi_vault 3+, amazon.aws 5+, azure.azcollection 2+, CI secret scanner (trufflehog, gitleaks, detect-secrets)
---

# Ansible Vault Hygiene (Intermediate)

Make secret handling boring and auditable. The playbook references a secret; it does not know how to print, persist, or rotate it.

## Core Engineering Capabilities

- Organize clear variable names that point to encrypted `vault.yml` values with vault-id per environment.
- Use Vault IDs, external secret lookups (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault), and environment-injected credentials.
- Scan repositories and CI artifacts for leaked passwords, keys, tokens, and private material with trufflehog/gitleaks.
- Enforce `no_log: true` boundaries; understand that `no_log` reduces diagnostics and compensate with sanitized status reporting.
- Rotate compromised credentials via vault-id rekey; scanning is not remediation.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- **Never commit plaintext secrets, decrypted vault files, vault passwords, or secrets in defaults, examples, fixtures, or CI artifacts.**
- **Use `no_log: true` on tasks and blocks that handle credentials.** Accept reduced diagnostics; add sanitized status tasks (`changed: true, msg: "Authentication configured"`) after secret tasks.
- **Keep secret variable names distinct from non-secret configuration.** Prefix vault refs with `vault_` (e.g., `vault_ansible_password`, `vault_snmp_community`). Never expose them through `debug`, registered output, facts, or failure text.
- **Rotate compromised credentials immediately; scanning is not remediation.** Delete from history with `git filter-repo` or BFG, rotate in source, re-encrypt.
- **Use least-privilege secret paths and verify external lookup behavior in CI.** HashiCorp Vault policies, AWS IAM roles, Azure RBAC must be scoped to the secret path only.
- **Vault password never in repo.** Inject via `ANSIBLE_VAULT_PASSWORD_FILE` (CI secret), `--vault-password-file` (local), or vault-id with external script.
- **Vault IDs required for multi-environment repos.** `dev`, `staging`, `prod` each with separate key. Encrypt with `--vault-id prod@vault_prod.py`.
- **Check-mode must not leak secrets.** Tasks with `no_log: true` must also handle `check_mode: true` without attempting connection.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Map every secret source: vault-id, variable file, environment variable, external provider (HashiCorp/AWS/Azure), log path, CI context. Identify values that must remain encrypted at rest vs values exposed to target modules. Define vault-id per environment and rotation schedule.

### Phase 2 (Implementation)

1. **Variable layering:** `vars/main.yml` (non-secret interfaces) → `vars/vault.yml` (encrypted refs) → external lookup at runtime.
2. **Vault-id structure:** `vault_ids: [dev@vault_dev.py, staging@vault_staging.py, prod@vault_prod.py]` in `ansible.cfg`. Each vault script reads password from CI secret or local keychain.
3. **Task boundaries:** Any task receiving, transforming, registering, or failing with secrets gets `no_log: true`. Follow with sanitized status task.
3. **External lookup tasks:** Use `community.hashi_vault.vault_kv2_get`, `amazon.aws.aws_secretsmanager`, `azure.azcollection.azure_keyvault_secret` with `no_log: true`. Cache in `set_fact` with `no_log: true`.
4. **CI scanning:** `trufflehog filesystem --fail --json` + `gitleaks detect --source . --verbose` in PR pipeline. Fail on any finding.

### Phase 3 (Verification)

Run leak scanner against source, logs, diffs, and failed-task output. Test: wrong vault IDs, missing secrets, check mode, accidental debug statements, external provider timeout/unauthorized. Confirm scanner catches known canaries without false confidence. Verify rotation: re-encrypt with new vault-id, deploy, verify old key revoked.

1. Classify secret fields and choose Vault or approved external provider per environment.
2. Reference `vault_` variables through clear, non-secret role interfaces (`netops_username`, `netops_password` → `vault_netops_password`).
3. Encrypt with vault-id, scan, syntax-check, test with injected CI credentials.
4. Review logs and artifacts for redaction before publishing results.
5. Document rotation procedure: `ansible-vault rekey --vault-id prod@new_script.py vars/vault.yml`.

## Production Code / Template Example

### Input / Requirement

Provide the secret inventory, vault layout per environment, CI/controller invocation, redaction requirements, and sanitized canary values for testing.

### Output / Generated Code

Return the encrypted-variable layout, playbook changes, invocation examples, leak-scan results, and a rotation/recovery runbook.

```yaml
# vars/main.yml (committed, non-secret)
netops_username: "netops"
snmp_version: "3"
snmp_security_level: "authPriv"

# Interface for roles/tasks
frr_bgp_password: "{{ vault_frr_bgp_password }}"
wireguard_private_key: "{{ vault_wireguard_private_key }}"
aci_apikey: "{{ vault_aci_apikey }}"
```

```yaml
# vars/vault.yml (encrypted with vault-id prod@vault_prod.py)
vault_frr_bgp_password: "ENCRYPTED"
vault_wireguard_private_key: "ENCRYPTED"
vault_aci_apikey: "ENCRYPTED"
```

```yaml
# tasks/configure_bgp.yml
- name: Configure BGP peer authentication
  no_log: true
  ansible.builtin.ios_config:
    lines:
      - "neighbor {{ bgp_peer }} password {{ vault_frr_bgp_password }}"
    parents: "router bgp {{ local_as }}"

- name: Report BGP auth status (sanitized)
  ansible.builtin.set_fact:
    bgp_auth_configured: true
  when: not ansible_check_mode

- name: Sanitized status output
  ansible.builtin.debug:
    msg: "BGP peer authentication configured for {{ bgp_peer }}"
  when: bgp_auth_configured is defined
```

```yaml
# tasks/external_lookup.yml
- name: Fetch ACI API key from HashiCorp Vault
  no_log: true
  community.hashi_vault.vault_kv2_get:
    url: "{{ vault_addr }}"
    token: "{{ lookup('env', 'VAULT_TOKEN') }}"
    path: "secret/data/netops/aci"
    engine_mount_point: "secret"
  register: aci_secret
  no_log: true

- name: Set ACI API key fact (no_log)
  no_log: true
  ansible.builtin.set_fact:
    vault_aci_apikey: "{{ aci_secret.data.data.apikey }}"
```

```yaml
# ansible.cfg
[defaults]
vault_identity_list = dev@vault_dev.py, staging@vault_staging.py, prod@vault_prod.py
vault_password_file = .vault_pass  # only for local dev, gitignored

[vault_id_match]
dev = ^dev-
staging = ^staging-
prod = ^prod-
```

```python
# vault_prod.py (executable, not committed)
#!/usr/bin/env python3
import os, sys
# Read from CI secret or local keychain
password = os.environ.get("ANSIBLE_VAULT_PASSWORD_PROD")
if not password:
    # Fallback: macOS keychain, pass, etc.
    import subprocess
    result = subprocess.run(["pass", "show", "ansible/vault/prod"], capture_output=True, text=True)
    password = result.stdout.strip()
print(password)
```

```yaml
# .github/workflows/secret-scan.yml
jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --fail --json
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        with:
          args: detect --source . --verbose --redact
      - name: Ansible Vault verify
        run: |
          ansible-vault view vars/vault.yml --vault-id prod@vault_prod.py
        env:
          ANSIBLE_VAULT_PASSWORD_PROD: ${{ secrets.ANSIBLE_VAULT_PASSWORD_PROD }}
```

## Validation, Linting & Testing Commands

- **Leak scan:** `trufflehog filesystem --fail --json .` && `gitleaks detect --source . --verbose --redact`
- **Vault syntax:** `ansible-vault view vars/vault.yml --vault-id prod@vault_prod.py` (in secure context only)
- **Test missing/expired secrets:** Run playbook with wrong vault-id; verify error does not echo values.
- **Test check-mode:** `ansible-playbook site.yml --check` — no secret tasks should execute or leak.
- **Test external provider failure:** Mock Vault 403/timeout; verify playbook fails cleanly without secret in output.
- **Rotation drill:** `ansible-vault rekey --vault-id prod@new_script.py vars/vault.yml`; deploy; verify old key revoked.
- Run `python3 scripts/validate_skills.py` from repository root.

## References

- [Ansible Vault guide](https://docs.ansible.com/projects/ansible/latest/vault_guide/index.html)
- [Ansible no_log](https://docs.ansible.com/projects/ansible/latest/reference_appendices/logging.html)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)
- [Gitleaks](https://github.com/gitleaks/gitleaks)
- [community.hashi_vault](https://docs.ansible.com/ansible/latest/collections/community/hashi_vault/)

## Offline Execution Contract

Secret scanning and variable-structure checks work locally. Without Ansible Vault or an external secret provider, use placeholders and test redaction; never substitute plaintext credentials.

## Architecture & Technical Design Patterns

**Three-layer naming pattern:**
1. Role interface variables (non-secret): `netops_username`, `bgp_peer`, `snmp_version`
2. Secret references (vault-prefixed): `vault_netops_password`, `vault_frr_bgp_password`, `vault_wireguard_private_key`
3. Provider lookup (runtime, no_log): `community.hashi_vault.vault_kv2_get`, `lookup('env', 'NETOPS_TOKEN')`

**Vault-id per environment:** Separate encryption keys for `dev`, `staging`, `prod`. CI injects password via env var to vault script. `ansible.cfg` maps directory prefixes to vault-ids.

**no_log boundaries:** Every task that touches a secret value gets `no_log: true`. Immediately follow with a sanitized `debug` or `set_fact` that confirms action without exposing data.

**Check-mode safety:** Tasks with `no_log: true` must handle `when: not ansible_check_mode` or use `ansible.builtin.set_fact` with `no_log: true` for check-mode simulation.

**Rotation runbook:** Documented procedure: 1) Generate new key, 2) `ansible-vault rekey`, 3) Update CI secret, 4) Deploy to staging, 5) Verify, 6) Deploy to prod, 7) Revoke old key in provider.

**CI artifact hygiene:** `actions/upload-artifact` with `retention-days: 1` for logs. Never upload vault files. Scan artifacts before upload.

## Tool Version Compatibility

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| Ansible Core | 2.15+ | Vault operations | `vault_identity_list` requires 2.14+ |
| ansible-vault | bundled | Encryption/decryption | AES256 default |
| trufflehog | 3.x | Secret scanning | `--fail --json` for CI |
| gitleaks | 8.x | Secret scanning | `--redact` for safe logs |
| HashiCorp Vault | 1.13+ | External secrets | KV v2 engine |
| AWS Secrets Manager | API v1 | External secrets | IAM role auth |
| Azure Key Vault | API 7.3 | External secrets | Managed identity |

**Notes:**
- TruffleHog 3.x has different CLI flags than 2.x
- Gitleaks 8.x uses new config format
- Ansible Vault rekey requires same cipher (AES256)

## Related Skills

- [ansible-role-scaffolding](ansible-role-scaffolding.md) — Vault variable structure in role defaults
- [ansible-execution-envs](ansible-execution-envs.md) — Vault password injection in EE builds
- [ansible-terraform-role](ansible-terraform-role.md) — Terraform output secrets into Ansible Vault
- [network-change-runbooks](network-change-runbooks.md) — Secret handling in change execution
- [ncclient-restconf](ncclient-restconf.md) — NETCONF/RESTCONF credential management