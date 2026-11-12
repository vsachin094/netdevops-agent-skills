---
name: vault-network-secrets
description: "[Tier: Intermediate] Manage network device credentials and secrets in HashiCorp Vault — KV v2 secret storage, AppRole authentication, transit encryption, lease renewal, and audit logging. Use this skill when network automation needs a centralized, auditable secret store instead of hardcoded passwords or env vars on runner hosts."
license: MIT
compatibility: HashiCorp Vault 1.10+; Python 3.9+; hvac library; AppRole or token auth; KV v2 secrets engine; network device credentials (SSH passwords, enable secrets, SNMPv3 keys, API tokens)
---

# Vault Network Secrets (Intermediate)

Store and retrieve network device credentials from HashiCorp Vault with audit logging, lease management, and credential rotation.

## Core Engineering Capabilities

- Store device credentials (SSH passwords, enable secrets, SNMPv3 auth/priv keys, API tokens) in Vault KV v2 with versioning.
- Authenticate automation runners via AppRole (short-lived, role-based) or token auth; avoid long-lived root tokens.
- Use Vault transit secrets engine to encrypt sensitive config fields before storing them in Git or config management.
- Retrieve secrets at runtime with lease renewal and short-lived tokens; never log or print secret values.
- Rotate credentials on a schedule; update Vault and the downstream inventory together.
- Enable Vault audit device logging for every secret access (who, what, when, from where).
- Integrate with Netmiko, Nornir, or Ansible by fetching credentials from Vault at runtime instead of reading from files.

## Architecture & Technical Design Patterns

```
automation runner
        │
        ▼
   Vault auth (AppRole / token)
        │
        ▼
   Vault KV v2 read (secret/data/network/...)
        │
        ▼
   short-lived credential in memory
        │
        ▼
   device connection (Netmiko / Nornir / Ansible)
        │
        ▼
   audit log entry (Vault audit device)
```

Keep one Vault path per environment or team (e.g., `secret/data/network/prod`, `secret/data/network/staging`). Use Vault policies to restrict each automation identity to only the paths it needs. Cache retrieved credentials in memory for the duration of a single run; do not write them to disk.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never store root tokens, unencrypted passwords, or private keys in Git, CI variables, or runner env vars. Use AppRole with role_id and secret_id injected at runtime.
- Do not print, log, or return secret values in task output, CLI stdout, or error messages. Redact them before writing results.
- Treat Vault as the source of truth for credentials; do not keep a parallel secrets file (`.env`, `secrets.yml`, `passwords.csv`) that can drift out of sync.
- Rotate device passwords and SNMPv3 keys through Vault; update the automation inventory and device in the same change window.
- Confirm Vault ACL policies grant least privilege: an identity that only reads `network/prod` must not write to `network/staging` or manage auth methods.
- Test Vault connectivity, auth, and read permissions in a non-production Vault namespace before pointing production automation at it.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: Vault address and namespace, auth method (AppRole or token), KV v2 mount path, secrets to store (device host, username, password, enable secret, SNMPv3 keys), Vault policies per automation identity, audit log destination, and rotation interval.

### Phase 2 (Implementation)

Write secrets into Vault KV v2, create AppRole roles and policies, implement the credential-fetching helper in the automation runner, and wire it into the device connection logic. Enable audit logging.

### Phase 3 (Verification)

Verify that the runner can authenticate, read the correct secret path, connect to a device using the fetched credential, and that the access appears in the Vault audit log. Test that a missing or revoked credential fails closed (connection refused, not fallback to plaintext).

### Input / Requirement

HashiCorp Vault instance, KV v2 engine enabled, AppRole credentials, network device inventory referencing Vault paths.

### Output / Generated Code

Vault policy files, AppRole role definition, credential-fetch helper code, updated inventory referencing Vault paths, and audit log configuration.

## Production Code / Template Example

```python
# Fetch network device credentials from Vault KV v2 (illustrative values)
import os
import hvac

def get_device_creds(vault_addr, role_id, secret_id, mount, path):
    client = hvac.Client(url=vault_addr)
    client.auth_approle.login(role_id=role_id, secret_id=secret_id)
    resp = client.secrets.kv.v2.read_secret_version(path=path, mount_point=mount)
    data = resp["data"]["data"]
    return {
        "host": data.get("host"),
        "username": data.get("username"),
        "password": data.get("password"),
        "secret": data.get("enable_secret"),
    }

# Example Vault secret (write once via CLI or API):
# vault kv put network/prod/core-sw-01 host=10.0.0.1 username=admin password=... enable_secret=...
```

## Validation, Linting & Testing Commands

- `python -m compileall` plus `ruff check` / `mypy` on Vault integration modules.
- Unit tests with mocked hvac client: successful read, AppRole login failure, missing path, lease renewal, redacted output.
- Integration test against a dev Vault server: write a secret, read it, rotate it, verify audit log entry.
- Audit log check: `vault audit list` and inspect audit device output for read events.
- `python3 scripts/validate_skills.py` from the repository root.

## References

- [HashiCorp Vault documentation](https://developer.hashicorp.com/vault/docs)
- [Vault KV v2 secrets engine](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2)
- [Vault AppRole auth method](https://developer.hashicorp.com/vault/docs/auth/approle)
- [Vault transit secrets engine](https://developer.hashicorp.com/vault/docs/secrets/transit)
- [hvac Python client](https://hvac.readthedocs.io/)

## Offline Execution Contract

Policy authoring, AppRole role design, and offline code review require no Vault. Live Vault auth, secret read/write, and audit log verification require a Vault instance (dev server or production); mark cross-version behavior unverified until tested.

## Related Skills

- [netmiko-core](../netmiko-core/SKILL.md) — device connections that consume credentials fetched from Vault
- [ansible-vault-hygiene](../ansible-vault-hygiene/SKILL.md) — Ansible Vault as an alternative for file-based secret encryption
- [network-change-runbooks](../network-change-runbooks/SKILL.md) — change execution that can consume Vault-sourced credentials
