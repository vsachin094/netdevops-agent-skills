---
name: netops-cli-packaging
description: "[Tier: Expert] Package network automation as installable Python CLIs with pyproject.toml, Typer or Click, Rich output, structured logging, and operational controls. Use this skill when a script must become a versioned internal tool with dry-run, inventory, limit, verbose, and CI-friendly behavior."
license: MIT
compatibility: Python 3.10+; pyproject.toml; Typer or Click; Rich; standard logging; pytest optional
---

# NetOps CLI Packaging (Expert)

Turn an automation workflow into a predictable operator interface. The CLI
must expose scope, authorization, output, and failure semantics instead of
burying them in Python flags or environment-specific assumptions.

## Core Engineering Capabilities

- Create a standards-based package with `pyproject.toml`, console entry point,
  versioning, dependency constraints, and test layout.
- Implement `--dry-run`, `--limit`, `--inventory`, `--verbose`, structured JSON
  output, Rich tables, progress, and exit codes.
- Separate CLI parsing, orchestration, transport, domain logic, and reporting
  so the code remains importable and testable.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Default to read-only or dry-run. Require an explicit mutation flag and show
  target scope before making changes.
- Validate inventory paths, limits, mutually exclusive flags, and credentials
  before connecting to devices.
- Use Rich for human output but keep JSON logs stable and free of ANSI codes
  for CI and log shipping.
- Return non-zero exit codes for validation errors, partial failures, and
  policy violations; document the contract.
- Pin or bound dependencies and test the packaged wheel in a clean environment.
- Never log passwords, tokens, private keys, or unredacted device output.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define operator commands, flags, exit codes, and read/write boundaries.
2. Build a typed settings object from CLI and environment inputs.
3. Validate scope, execute the domain service, and stream human progress.
4. Emit a final summary and machine-readable result, then exit according to
   the documented policy.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
import typer

app = typer.Typer()

@app.command()
def run(inventory: str, limit: int = 0, dry_run: bool = True, verbose: bool = False):
    """Run a bounded network operation."""
    if limit < 0:
        raise typer.BadParameter("limit must be non-negative")
    settings = Settings(inventory=inventory, limit=limit, dry_run=dry_run, verbose=verbose)
    result = execute(settings)
    raise typer.Exit(code=0 if result.failed == 0 else 2)
```

## Validation, Linting & Testing Commands

- Test CLI help, invalid combinations, dry-run behavior, output modes, exit
  codes, and Ctrl-C handling.
- Build and install the wheel in a clean virtual environment.
- Run `ruff`, `mypy` where adopted, and pytest without live device access.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Typer documentation](https://typer.tiangolo.com/)
- [Click documentation](https://click.palletsprojects.com/)
- [Rich documentation](https://rich.readthedocs.io/)
- [Python packaging guide](https://packaging.python.org/en/latest/)

## Offline Execution Contract

CLI behavior can be tested locally with fake services and fixtures. If Typer, Click, Rich, or packaging tools are missing, keep the command contract and standard-library service layer usable and report the missing build dependency.

## Architecture & Technical Design Patterns

Define a CLI contract before implementation: command name, required options,
defaults, mutually exclusive flags, exit codes, stdout/stderr behavior, and
JSON schema. Recommended controls are `--inventory`, `--limit`, `--dry-run`,
`--output human|json`, `--verbose`, and `--timeout`. Parse into an immutable
settings object, validate before opening connections, and pass settings into a
service function that is testable without Typer/Click.

Use exit code `0` for complete success, `1` for usage/validation error, `2`
for partial or operational failure, and `130` for cancellation unless the
project has an established convention. Human output may use Rich; JSON output
must not contain ANSI codes and must include per-target status, error type,
duration, and summary counts. Package an entry point through
`[project.scripts]` and test the installed wheel, not only source execution.
