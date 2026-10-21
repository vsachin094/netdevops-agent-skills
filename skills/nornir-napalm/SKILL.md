---
name: nornir-napalm
description: "[Tier: Advanced] Build multi-vendor Nornir automation with NAPALM, Netmiko, Scrapli, and Jinja2 for inventory-driven reads and transactional configuration workflows. Use this skill when a network job must scale beyond a single script while preserving per-host results, diffs, commit controls, and rollback behavior."
license: MIT
compatibility: Python 3.10+; Nornir; NAPALM; nornir_napalm or nornir_netmiko; Jinja2; YAML inventory
---

# Nornir/NAPALM (Advanced)

Separate inventory, intent, transport, tasks, and reporting. Nornir provides
execution and aggregation; NAPALM provides a vendor-neutral interface where
the platform actually supports the getter or config operation.

## Core Engineering Capabilities

- Maintain `config.yaml`, `hosts.yaml`, `groups.yaml`, and `defaults.yaml`
  inventory with platform-specific connection data separated from intent.
- Run getters, parsed commands, templated configuration, configuration diffs,
  commit/discard workflows, and per-host result aggregation.
- Compose Nornir processors, filters, retries, and structured reporting for
  controlled fleet operations.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Keep secrets outside inventory files; use environment, vault, or an approved
  credential plugin.
- Generate candidate configuration and call `compare_config()` before
  `commit_config()`. A non-empty diff requires explicit change authorization.
- Call `discard_config()` on failure and ensure cleanup in `finally` paths.
- Never let one host exception abort the fleet. Preserve host, task, exception,
  diff, and timing in the result.
- Do not assume every NAPALM getter or replace operation is supported equally;
  use a driver capability matrix and fall back to a tested vendor task.
- Keep inventory groups declarative and avoid embedding environment-specific
  branching in task functions.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Validate inventory and filter the intended host set.
2. Run read-only prechecks and collect a baseline.
3. Render candidate configuration, generate per-host diffs, and stop on policy
   violations or unexpected changes.
4. Commit only after approval, then run postchecks and produce an aggregate
   report. Discard candidate state on errors.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_napalm.plugins.tasks import napalm_get

nr = InitNornir(config_file="config.yaml")
candidate = nr.run(task=napalm_configure, configuration="interface Loopback100\n description managed", dry_run=True)
for host, result in candidate.items():
    if result.failed:
        continue
    print(host, result.result)
```

The exact task/plugin signature is version-specific; verify it against the
installed Nornir and NAPALM versions and test the dry-run path before commit.

## Validation, Linting & Testing Commands

- Test inventory parsing, host filtering, task failure isolation, diff output,
  discard behavior, and postcheck failures.
- Run a disposable lab or mocked driver before production changes.
- Assert that the number of results equals the number of targeted hosts.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Nornir documentation](https://nornir.readthedocs.io/)
- [NAPALM documentation](https://napalm.readthedocs.io/)
- [nornir-napalm](https://github.com/danielberkompas/nornir-napalm)

## Offline Execution Contract

Use local inventory fixtures, mocked drivers, and rendered diffs to verify orchestration. Without Nornir/NAPALM or devices, validate task composition and transaction policy but do not claim commit or discard behavior was exercised.

## Architecture & Technical Design Patterns

Use four inventory layers: `config.yaml` selects the runner and processors;
`hosts.yaml` contains identity and host data; `groups.yaml` contains shared
platform/transport data; `defaults.yaml` contains safe defaults. Keep
`hostname`, `platform`, `port`, `username`, and `password` references separate
from service intent. Filter targets before running any task and print the
resolved host list in dry-run mode.

For NAPALM changes, the reliable sequence is `load_merge` or `load_replace`,
`compare_config`, approval, `commit_config`, postcheck; on exception call
`discard_config` and record whether discard itself succeeded. Treat
`result.failed`, `result.exception`, and nested task failures as first-class
data. Use `nr.run()` result aggregation rather than shared mutable globals.
Use vendor-specific Nornir tasks only where the NAPALM driver lacks the needed
getter or operation, and keep that exception documented per platform.
