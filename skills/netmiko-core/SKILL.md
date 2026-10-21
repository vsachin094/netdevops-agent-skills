---
name: netmiko-core
description: "[Tier: Basic] Generate safe Python Netmiko automation for SSH command execution, configuration changes, running-config backups, and structured device results. Use this skill when a small synchronous network script needs explicit credential handling, command/config separation, and dry-run-friendly behavior."
license: MIT
compatibility: Python 3.10+; netmiko 4+; optional python-dotenv and pytest; SSH reachability to target devices
---

# Netmiko Core (Basic)

Write a focused script that is safe to review and easy to remove. Netmiko is
the transport and device-driver layer; it is not an inventory system, secret
manager, transaction engine, or substitute for a change workflow.

## Core Engineering Capabilities

- Connect to Cisco IOS-XE/NX-OS, Arista EOS, Junos, and other supported
  platforms using `ConnectHandler`.
- Execute read-only commands, retrieve configurations, and apply explicit
  configuration sets with structured per-device results.
- Use context managers, timeouts, session logging controls, and exception
  handling appropriate to a single-device or small-batch script.
- Support `--dry-run`, environment-based credentials, and machine-readable
  JSON output where the workflow requires it.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never hardcode passwords, tokens, enable secrets, or private keys. Read them
  from a secret manager, environment variable, or `getpass` prompt.
- Use `with ConnectHandler(**device) as conn:` so sessions close on every path.
- Keep `send_command()` for operational reads and `send_config_set()` for
  intended configuration changes. Never pass untrusted input directly into a
  config command list.
- Set `conn_timeout`, `banner_timeout`, `auth_timeout`, and command timeouts
  deliberately. A timeout is a device result, not a reason to retry forever.
- Make changes opt-in, show the rendered command set in dry-run mode, and
  record the device, command, result, and exception class without secrets.
- Do not parse output with positional string splits when a tested parser or
  structured API is available. Preserve raw output only under an approved
  retention policy.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define inventory fields, platform type, read/write intent, timeout policy,
   and expected result schema.
2. Load credentials securely and validate required device fields before making
   a connection.
3. Run pre-checks and, for changes, expose a dry-run command preview.
4. Connect with a context manager, collect output, apply configuration only
   after explicit authorization, and verify the post-state.
5. Return one structured result per device; exit non-zero when any required
   device failed.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
import os
from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "192.0.2.10",
    "username": os.environ["NETOPS_USERNAME"],
    "password": os.environ["NETOPS_PASSWORD"],
    "conn_timeout": 10,
}

with ConnectHandler(**device) as conn:
    before = conn.send_command("show ip interface brief", read_timeout=30)
    if not dry_run:
        conn.send_config_set(["interface Loopback100", "description managed-by-code"])
        after = conn.send_command("show running-config interface Loopback100")
```

## Validation, Linting & Testing Commands

- Run `python3 skills/netmiko-core/scripts/syntax_check.py path/to/script.py`.
- Unit-test command construction without opening SSH sessions.
- Test authentication failure, timeout, command failure, and partial output.
- Review logs for credentials and sensitive command output.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Netmiko documentation](https://ktbyers.github.io/netmiko/)
- [Netmiko GitHub repository](https://github.com/ktbyers/netmiko)

## Offline Execution Contract

Keep connection code separate from parsing and command construction. Without Netmiko or SSH access, run syntax checks and mocked command/result tests; never simulate a successful device change as if it were real.

## Architecture & Technical Design Patterns

Use a settings boundary and a device-type allow-list:

```python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Device:
    host: str
    device_type: str
    username: str
    password: str
    port: int = 22

device = Device(os.environ["NETOPS_HOST"], "cisco_ios",
                os.environ["NETOPS_USERNAME"], os.environ["NETOPS_PASSWORD"])
```

Read workflow: connect, `send_command`, parse, verify, disconnect. Write
workflow: render a list of commands, show it in dry-run, collect a precheck,
`send_config_set`, optionally `save_config`, then collect a postcheck. Catch
`NetmikoTimeoutException`, `NetmikoAuthenticationException`, and
`NetmikoBaseException` separately so reports distinguish reachability,
credentials, and device/driver errors. Use `read_timeout` for long commands,
`expect_string` only when the prompt is known, and never pass a shell command
through `send_command` when a structured API or parser is required.
