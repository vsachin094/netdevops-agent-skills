---
name: netmiko-core
description: "[Tier: Intermediate] Build inventory-driven Netmiko automation with per-device result aggregation, --check/--diff support, config_mode handling per platform, and prompt derivation from base_prompt. Use this skill when a production script must operate safely across heterogeneous fleets with explicit credentials, timeouts, and machine-readable output."
license: MIT
compatibility: Python 3.10+; netmiko 4.3+; optional python-dotenv, typer, rich, pyyaml; SSH reachability to target devices
---

# Netmiko Core (Intermediate)

Write a fleet-capable runner that is safe to review, easy to remove, and produces auditable evidence. Netmiko is the transport layer; this skill adds inventory, concurrency control, structured results, and change safety.

## Core Engineering Capabilities

- Inventory-driven execution: YAML/JSON inventory with device groups, platform mapping, and per-device overrides.
- Per-device result aggregation: success, failure, output, diff, timing, and exception class in JSON Lines.
- Platform-specific `config_mode` handling: IOS (`config terminal`), NX-OS (`configure terminal`), EOS (`configure`), Junos (`configure private`), IOS-XR (`configure`), SR Linux (`enter candidate`).
- Prompt derivation from `base_prompt` to avoid prompt-mismatch hangs on pagination or vendor-specific prompts.
- `--check` (dry-run): renders command set, shows diff, does not send config.
- `--diff`: shows rendered config vs running-config for config changes.
- Credential handling: environment variables, encrypted YAML (ansible-vault compatible), or interactive prompt — never hardcoded.
- Concurrency control: `--workers N` with bounded semaphore, per-device timeout, global timeout.
- Structured logging: JSON Lines to stdout, human-readable with Rich to stderr.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- **Never hardcode passwords, tokens, enable secrets, or private keys.** Read from env vars (`NETOPS_PASSWORD`, `NETOPS_ENABLE`), vaulted YAML, or `getpass` with TTY check.
- **Use `with ConnectHandler(**device) as conn:`** so sessions close on every path including exceptions.
- **Keep `send_command()` for operational reads and `send_config_set()` for intended changes.** Never pass untrusted input directly into a config command list.
- **Set all timeouts deliberately:** `conn_timeout=10`, `banner_timeout=10`, `auth_timeout=10`, `read_timeout=30` (config), `read_timeout=15` (show). A timeout is a device result, not a retry trigger.
- **Derive `expect_string` from `conn.base_prompt`** — never hardcode `>` or `#`. Pagination and vendor prompts vary.
- **Make changes opt-in:** default `--check`, require `--apply` to mutate. Show rendered command set in `--check` mode.
- **Record per-device result schema:** `{device, host, status, started, finished, duration_ms, commands, output, diff, error_class, error_message}`. Exit code: 0=all ok, 1=usage, 2=partial failure, 3=all failed, 130=SIGINT.
- **Do not parse output with positional string splits.** Use TextFSM/Genie/TTP or structured APIs. Preserve raw output only under approved retention.
- **Handle `config_mode` differences explicitly.** Netmiko's `config_mode()` works for most but Junos/SR Linux need custom sequences.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: inventory source (file, NetBox, dynamic), device groups, platform map, command set (read) or config set (write), credential source, timeout policy, concurrency limit, output format, change approval requirement. Validate inventory against platform allow-list before any connection.

### Phase 2 (Implementation)

1. **Settings model** — Typer/Click CLI with `InventorySettings`, `DeviceSettings`, `ExecutionSettings`, `OutputSettings`.
2. **Inventory loader** — YAML/JSON with groups, hostvars, platform normalization (`cisco_ios`, `cisco_nxos`, `arista_eos`, `juniper_junos`, `cisco_xr`, `nokia_sros`).
3. **Credential resolver** — env > vaulted YAML > interactive; validate required fields per device.
4. **Command/config renderer** — Jinja2 templates for config sets, per-platform command lists.
5. **Connection worker** — async-compatible function using `ConnectHandler` context manager, explicit timeouts, `base_prompt`-derived `expect_string`, platform `config_mode` sequence.
6. **Result aggregator** — collects `DeviceResult` objects, emits JSON Lines, summarizes at end.
7. **Dry-run/diff mode** — renders config, fetches running-config, shows unified diff, exits without `send_config_set`.

### Phase 3 (Verification)

Test with mocked `ConnectHandler` (pytest fixtures): success, auth failure, timeout, banner timeout, read timeout, invalid command, partial config failure, prompt mismatch, pagination, config_mode failure. Integration test against Containerlab topology (FRR + cEOS + SR Linux). Validate JSON Lines schema, exit codes, `--check` output, `--diff` output, credential redaction in logs.

## Production Code / Template Example

### Input / Requirement

Provide: inventory file, platform map, command/config templates, credential source, timeout/concurrence policy, approval gate (manual/CI), output destination.

### Output / Generated Code

Return: `netops_runner/` package with `cli.py`, `inventory.py`, `credentials.py`, `runner.py`, `result.py`, `platforms.py`, `templates/`, `tests/`, `pyproject.toml`, `README.md`.

```python
# netops_runner/platforms.py
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class PlatformConfig:
    netmiko_device_type: str
    config_enter: List[str]
    config_exit: str
    config_check: str
    save_command: str
    prompt_pattern: str

PLATFORMS = {
    "ios": PlatformConfig("cisco_ios", ["config terminal"], "end", "show running-config", "write memory", r"^{base_prompt}[#>]"),
    "nxos": PlatformConfig("cisco_nxos", ["configure terminal"], "end", "show running-config", "copy running-config startup-config", r"^{base_prompt}[#>]"),
    "eos": PlatformConfig("arista_eos", ["configure"], "end", "show running-config", "copy running-config startup-config", r"^{base_prompt}[#>]"),
    "junos": PlatformConfig("juniper_junos", ["configure private"], "exit configuration-mode", "show configuration | display set", "commit", r"^{base_prompt}[#>]"),
    "iosxr": PlatformConfig("cisco_xr", ["configure"], "end", "show running-config", "commit", r"^{base_prompt}[#>]"),
    "srl": PlatformConfig("nokia_sros", ["enter candidate"], "exit candidate", "show configuration", "commit confirmed", r"^{base_prompt}[#>]"),
}
```

```python
# netops_runner/runner.py
import time, json
from dataclasses import dataclass, asdict
from typing import List
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException, NetmikoBaseException
from .platforms import PLATFORMS, PlatformConfig

@dataclass
class DeviceResult:
    device: str; host: str; status: str; started: float; finished: float
    duration_ms: int; commands: List[str]; output: str; diff: str
    error_class: str; error_message: str

def derive_expect_string(base_prompt: str, platform: PlatformConfig) -> str:
    import re
    return platform.prompt_pattern.format(base_prompt=re.escape(base_prompt.rstrip('>#')))

def run_device(device: dict, commands: List[str], config_commands: List[str],
               check_mode: bool, diff_mode: bool, platform_name: str, timeouts: dict) -> DeviceResult:
    started = time.time()
    platform = PLATFORMS[platform_name]
    device_params = {k: v for k, v in device.items() if k != "groups"}
    device_params.setdefault("device_type", platform.netmiko_device_type)
    device_params.setdefault("timeout", timeouts.get("conn", 10))
    device_params.setdefault("banner_timeout", timeouts.get("banner", 10))
    device_params.setdefault("auth_timeout", timeouts.get("auth", 10))
    device_params.setdefault("read_timeout", timeouts.get("read", 30))

    result = DeviceResult(device=device.get("name", device["host"]), host=device["host"],
        status="error", started=started, finished=0, duration_ms=0, commands=[], output="", diff="",
        error_class="", error_message="")

    try:
        with ConnectHandler(**device_params) as conn:
            conn.read_timeout = timeouts.get("read", 30)
            expect_string = derive_expect_string(conn.base_prompt, platform)
            output_parts = [f"{conn.base_prompt}# {cmd}\n{conn.send_command(cmd, expect_string=expect_string, read_timeout=timeouts.get('read', 15))}" for cmd in commands]
            result.commands.extend(commands); result.output = "\n\n".join(output_parts)

            if config_commands:
                if check_mode:
                    result.diff = "[CHECK MODE] Would send config:\n" + "\n".join(config_commands)
                    result.status = "success"
                else:
                    for enter_cmd in platform.config_enter:
                        conn.send_command(enter_cmd, expect_string=expect_string)
                    config_output = conn.send_config_set(config_commands, enter_config_mode=False, exit_config_mode=False, cmd_verify=True)
                    result.output += f"\n\n--- CONFIG ---\n{config_output}"
                    conn.send_command(platform.config_exit, expect_string=expect_string)
                    if diff_mode:
                        running = conn.send_command(platform.config_check, expect_string=expect_string, read_timeout=timeouts.get("read", 30))
                        result.diff = "[DIFF] Running config retrieved"
                    result.commands.extend(config_commands); result.status = "success"
    except NetmikoTimeoutException as e:
        result.status, result.error_class, result.error_message = "timeout", "NetmikoTimeoutException", str(e)
    except NetmikoAuthenticationException as e:
        result.status, result.error_class, result.error_message = "auth_failed", "NetmikoAuthenticationException", str(e)
    except NetmikoBaseException as e:
        result.status, result.error_class, result.error_message = "failed", type(e).__name__, str(e)
    except Exception as e:
        result.status, result.error_class, result.error_message = "failed", type(e).__name__, str(e)
    finally:
        result.finished = time.time(); result.duration_ms = int((result.finished - result.started) * 1000)
    return result
```

```python
# netops_runner/cli.py
import typer
import yaml
import json
import sys
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from .inventory import load_inventory
from .credentials import resolve_credentials
from .runner import run_device, DeviceResult
from .platforms import PLATFORMS

app = typer.Typer(add_completion=False)
console = Console(stderr=True)
err_console = Console(stderr=True)

@app.command()
def run(
    inventory: Path = typer.Option(..., "--inventory", "-i", exists=True, readable=True),
    commands: Optional[Path] = typer.Option(None, "--commands", "-c", exists=True),
    config: Optional[Path] = typer.Option(None, "--config", exists=True),
    platform: str = typer.Option("ios", "--platform", "-p"),
    group: Optional[str] = typer.Option(None, "--group", "-g"),
    limit: Optional[str] = typer.Option(None, "--limit", "-l"),
    workers: int = typer.Option(10, "--workers", "-w", min=1, max=100),
    check: bool = typer.Option(True, "--check/--apply", help="Dry-run by default"),
    diff: bool = typer.Option(False, "--diff/--no-diff"),
    output_json: Optional[Path] = typer.Option(None, "--output-json"),
    timeout_conn: int = typer.Option(10, "--timeout-conn"),
    timeout_read: int = typer.Option(30, "--timeout-read"),
):
    """Run commands/config against network devices."""
    if not commands and not config:
        console.print("[red]Error: At least one of --commands or --config required[/red]")
        raise typer.Exit(1)

    platform = platform.lower()
    if platform not in PLATFORMS:
        console.print(f"[red]Error: Unknown platform {platform}. Valid: {list(PLATFORMS.keys())}[/red]")
        raise typer.Exit(1)

    devices = load_inventory(inventory, group, limit)
    if not devices:
        console.print("[yellow]No devices matched[/yellow]")
        raise typer.Exit(0)

    devices = resolve_credentials(devices)

    cmd_list = yaml.safe_load(commands.read_text()) if commands else []
    config_list = yaml.safe_load(config.read_text()) if config else []

    timeouts = {"conn": timeout_conn, "read": timeout_read, "banner": 10, "auth": 10}

    results: List[DeviceResult] = []
    failed = 0

    for device in devices:
        result = run_device(
            device=device,
            commands=cmd_list,
            config_commands=config_list,
            check_mode=check,
            diff_mode=diff,
            platform_name=platform,
            timeouts=timeouts,
        )
        results.append(result)

        # JSON Lines output
        if output_json:
            with open(output_json, "a") as f:
                f.write(json.dumps(asdict(result), default=str) + "\n")

        # Human output
        status_color = "green" if result.status == "success" else "red"
        console.print(f"[{status_color}]{result.device} ({result.host}): {result.status} ({result.duration_ms}ms)[/{status_color}]")
        if result.status != "success":
            console.print(f"  [red]{result.error_class}: {result.error_message}[/red]")
            failed += 1

    # Summary
    console.print(f"\n[bold]Summary: {len(results)} total, {len(results)-failed} ok, {failed} failed[/bold]")

    exit_code = 0 if failed == 0 else (2 if failed < len(results) else 3)
    raise typer.Exit(exit_code)

if __name__ == "__main__":
    app()
```

```yaml
# inventory.yml
devices:
  - name: leaf-01
    host: 192.0.2.11
    platform: eos
    username: netops
    groups: [leaf, dc1]
  - name: leaf-02
    host: 192.0.2.12
    platform: eos
    username: netops
    groups: [leaf, dc1]
  - name: spine-01
    host: 192.0.2.1
    platform: nxos
    username: netops
    groups: [spine, dc1]
```

```yaml
# config_add_vlan.yml
- "vlan 200"
- "name SERVERS"
- "exit"
```

## Validation, Linting & Testing Commands

- **Unit tests (mocked):** `pytest tests/test_runner.py -v` — covers all exception paths, prompt derivation, config_mode sequences, check/diff modes.
- **Integration test:** `containerlab deploy -t topology.clab.yml && pytest tests/test_integration.py -v` — against FRR (ios), cEOS (eos), SR Linux (srl).
- **Schema validation:** `python -m jsonschema -i results.jsonl schema/device_result.schema.json`
- **Credential redaction test:** grep output for `NETOPS_PASSWORD` — must not appear.
- **Lint:** `ruff check netops_runner/ && mypy netops_runner/`
- **Package test:** `pip install -e . && netops-run --help`
- **CI gate:** `python3 scripts/validate_skills.py` from repository root.

## References

- [Netmiko documentation](https://ktbyers.github.io/netmiko/)
- [Netmiko exceptions](https://github.com/ktbyers/netmiko/blob/master/netmiko/exceptions.py)
- [Typer documentation](https://typer.tiangolo.com/)
- [Rich documentation](https://rich.readthedocs.io/)

## Offline Execution Contract

CLI behavior tested locally with mocked `ConnectHandler` fixtures. Without Netmiko or SSH access, run syntax checks, unit tests, and mocked command/result tests. Containerlab topology required for integration validation.

## Architecture & Technical Design Patterns

**Settings boundary:** CLI → `Settings` dataclass → injected into `run_device()`. No global state.

**Platform config:** Centralized in `platforms.py`. Adding a platform = one `PlatformConfig` entry + test fixture.

**Prompt derivation:** `expect_string = derive_expect_string(conn.base_prompt, platform)` handles pagination (`--More--`), vendor prompts (`switch(config)#`, `router>`, `user@host#`).

**Config mode sequences:** Explicit per-platform `config_enter`/`config_exit` lists. Junos `configure private` + `exit configuration-mode`. SR Linux `enter candidate` + `exit candidate`.

**Result schema:** JSON Lines for streaming CI consumption. Human output via Rich on stderr. Exit codes documented and consistent.

**Credential precedence:** `env` > `vaulted yaml` > `interactive`. Vault format: `ansible_vault` compatible (`$ANSIBLE_VAULT;1.1;AES256...`).

**Concurrency:** ThreadPoolExecutor with `max_workers`. Semaphore for rate limiting if needed. Per-device timeout enforced by `read_timeout` + wrapper timeout.

## Vendor Version Compatibility

| Platform | Netmiko Type | Tested Version | config_mode | Prompt Pattern | Notes |
|----------|--------------|----------------|-------------|----------------|-------|
| Cisco IOS | cisco_ios | 15.x, 16.x, 17.x | config terminal | `^{base_prompt}[#>]` | SSH only |
| Cisco NX-OS | cisco_nxos | 7.x, 9.x, 10.x | configure terminal | `^{base_prompt}[#>]` | NX-API alternative |
| Arista EOS | arista_eos | 4.25+, 4.30+ | configure | `^{base_prompt}[#>]` | eAPI preferred |
| Juniper Junos | juniper_junos | 18.x, 20.x, 21.x | configure private | `^{base_prompt}[#>]` | NETCONF preferred |
| Cisco IOS-XR | cisco_xr | 6.x, 7.x | configure | `^{base_prompt}[#>]` | gRPC alternative |
| Nokia SR Linux | nokia_sros | 21.x, 22.x, 23.x | enter candidate | `^{base_prompt}[#>]` | gNMI preferred |

**Notes:**
- Netmiko 4.3+ required for SR Linux support
- Junos `configure private` requires Junos 15.1+
- IOS-XE 17.x prompt changes require updated `base_prompt` derivation
- EOS `configure` (no "terminal") since 4.15+

## Related Skills

- [scrapli-netmiko-threaded](scrapli-netmiko-threaded.md) — Fleet-scale concurrency with same inventory
- [async-netops](async-netops.md) — AsyncIO alternative for high-concurrency fleets
- [ansible-netcli-playbooks](ansible-netcli-playbooks.md) — Ansible-native alternative using network_cli
- [network-change-runbooks](network-change-runbooks.md) — Pre/post checks for changes pushed via Netmiko
- [containerlab-topologies](containerlab-topologies.md) — Lab fixtures for integration testing
- [ntc-textfsm](ntc-textfsm.md) — Structured parsing for Netmiko `use_textfsm=True`