---
name: paramiko-ssh
description: "[Tier: Intermediate] Build secure Paramiko-based SSH and SFTP transport for infrastructure automation, jump hosts, command execution, host-key verification, channel timeouts, and structured result handling. Use this skill when raw SSH transport is required and a higher-level network driver is unavailable or intentionally out of scope."
license: MIT
compatibility: Python 3.10+; Paramiko 3.x; OpenSSH-compatible server; pytest; local known_hosts or pinned host keys
---

# Paramiko SSH Transport (Intermediate)

Use Paramiko as a transport library, not as a substitute for a network-device
driver. If the task requires prompt-aware CLI configuration, privilege
escalation, paging, or vendor-specific command handling, prefer Netmiko or
Scrapli and use Paramiko only where raw SSH is the deliberate boundary.

## Core Engineering Capabilities

- Establish authenticated SSH sessions with strict host-key verification and
  explicit connect, banner, authentication, and channel timeouts.
- Execute bounded non-interactive commands and return stdout, stderr, exit
  status, duration, and target identity as a typed result.
- Open controlled interactive channels only when the protocol requires them;
  handle prompts, EOF, channel closure, and read timeouts explicitly.
- Support bastion or jump-host connections through a caller-supplied socket or
  ProxyCommand without exposing credentials in command lines.
- Transfer files with SFTP only when the workflow requires it, using atomic
  temporary paths, mode checks, size limits, and checksum verification.
- Provide testable connection factories so unit tests can use a local sshd,
  Paramiko test server, or a fake transport without touching production hosts.

## Architecture & Technical Design Patterns

Keep transport, authentication, command policy, and result normalization
separate:

```text
inventory + secret reference + known_hosts
                  │
                  ▼
          connection factory
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
  exec_command            SFTP/channel
       │                     │
       └──────────┬──────────┘
                  ▼
       typed result + audit metadata
```

Use `SSHClient.load_system_host_keys()` or an explicitly supplied reviewed
known_hosts file. The default policy must reject unknown keys. Build one client
per target or use a bounded pool with deterministic close behavior; do not
share a mutable client across unrelated worker threads.

For command execution, prefer `exec_command` with a fixed command template and
`get_pty=False`. Treat non-zero exit status as a failed operation and retain
stderr separately. Use an interactive `invoke_shell` channel only for a
documented protocol or prompt sequence. A network CLI that needs prompt
parsing, config mode, or paging belongs in Netmiko or Scrapli.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- HARD-BANNED: `AutoAddPolicy`, blind host-key acceptance, or disabling host
  key verification to make a connection succeed.
- HARD-BANNED: hardcoded passwords, private keys, tokens, or credentials in
  source, fixtures, command arguments, logs, or exception messages.
- HARD-BANNED: passing untrusted user input directly into a shell command,
  invoking a local shell to concatenate command strings, or using an
  interactive channel as a generic command runner.
- Require separate connect, banner, authentication, and channel timeouts;
  never allow a blocked read to hang a fleet worker indefinitely.
- Load keys from an approved agent, secret manager, or file with restrictive
  permissions. Do not log the resolved private-key path when it contains a
  sensitive user or workspace location.
- Close channels, SFTP sessions, and clients in `finally` blocks or context
  managers, including authentication and command failure paths.
- Bound command output and file-transfer size. Redact known secret patterns
  before persisting results or sending them to an agent.
- Do not claim a command changed a device unless the exit status, stderr, and
  postcondition have all been checked.
- Use a separate known_hosts file for tests; never weaken production trust
  policy because a lab fixture uses a generated key.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Confirm the target host, port, username source, authentication method,
known_hosts policy, command or file operation, timeout budget, output limit,
and whether the target is a server, appliance, or network device. Reject raw
passwords and reject a request that asks to bypass host-key verification.

### Phase 2 (Generation)

Create a small connection factory and a typed operation function. Use strict
host-key loading, fixed command templates, explicit timeout values, structured
logging, and context-managed cleanup. Select Netmiko or Scrapli instead when
the requested behavior depends on vendor CLI prompts or configuration modes.

### Phase 3 (Self-Verification)

Run the operation against a local sshd or test server with a known host key.
Exercise authentication failure, unknown host key, timeout, non-zero exit,
large output, interrupted transfer, and cleanup paths. Confirm that logs and
returned results contain no credentials.

## Production Code / Template Example

### Input / Requirement

Provide a target hostname, username and key reference, reviewed known_hosts
file, fixed command, timeout values, output limit, and the expected exit-status
and postcondition. Do not provide secrets in the prompt or source tree.

### Output / Generated Code

Return a reusable transport module with a typed result, strict trust policy,
bounded timeouts, redacted logging, and tests for success and failure paths.

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import time

import paramiko


@dataclass(frozen=True)
class CommandResult:
    host: str
    command: str
    stdout: str
    stderr: str
    exit_status: int
    elapsed_seconds: float


def run_command(host: str, command: str, known_hosts: Path) -> CommandResult:
    if command not in {"uname -a", "ip -j address show"}:
        raise ValueError("command is not in the approved command set")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.load_host_keys(str(known_hosts))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())

    started = time.monotonic()
    try:
        client.connect(
            hostname=host,
            port=int(os.environ.get("SSH_PORT", "22")),
            username=os.environ["SSH_USER"],
            key_filename=os.environ["SSH_KEY_FILE"],
            look_for_keys=False,
            allow_agent=False,
            timeout=10,
            banner_timeout=10,
            auth_timeout=10,
        )
        stdin, stdout, stderr = client.exec_command(command, timeout=20)
        del stdin
        output = stdout.read().decode("utf-8", errors="replace")
        error = stderr.read().decode("utf-8", errors="replace")
        status = stdout.channel.recv_exit_status()
        return CommandResult(
            host=host,
            command=command,
            stdout=output[:1_000_000],
            stderr=error[:64_000],
            exit_status=status,
            elapsed_seconds=time.monotonic() - started,
        )
    finally:
        client.close()
```

## Validation, Linting & Testing Commands

- Run `python -m compileall` and `ruff check` or the repository's configured
  Python linter.
- Test strict host-key rejection with an unknown or changed server key.
- Test authentication failure, connect timeout, channel timeout, non-zero exit,
  output truncation, and client cleanup.
- Run the operation against a disposable OpenSSH container or local sshd; do
  not use a production host as a unit-test target.
- Run `pytest` with secrets and real hostnames excluded from fixtures.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Paramiko documentation](https://docs.paramiko.org/en/latest/)
- [Paramiko SSHClient API](https://docs.paramiko.org/en/latest/api/client.html)
- [OpenSSH known_hosts format](https://man.openbsd.org/ssh_config)

## Offline Execution Contract

The skill can generate and test transport code offline with Paramiko, a local
sshd or test server, a known_hosts fixture, and synthetic command responses.
Without a reachable target, mark host-key, authentication, command behavior,
and remote postconditions as unverified.
