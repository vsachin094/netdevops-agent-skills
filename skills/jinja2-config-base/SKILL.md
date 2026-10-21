---
name: jinja2-config-base
description: "[Tier: Basic] Build foundational Jinja2 network configuration templates paired with clean YAML variables for AAA, NTP, syslog, SNMP, VLANs, and interfaces. Use this skill when a small, single-vendor configuration artifact needs strict data/template separation and deterministic rendering."
license: MIT
compatibility: Python 3.10+; Jinja2 3+; PyYAML; optional pytest and yamllint
---

# Jinja2 Configuration Base (Basic)

Keep the template concerned with presentation and the YAML model concerned
with intent. A rendered configuration must be deterministic, whitespace-safe,
and rejected when required input is missing.

## Core Engineering Capabilities

- Render common device stanzas from YAML or JSON data.
- Use macros and loops for repeated interfaces, VLANs, servers, and access
  lists without duplicating configuration text.
- Produce a reviewable rendered file and a machine-readable input model.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Configure `jinja2.StrictUndefined` so missing variables fail instead of
  producing `None`, empty commands, or malformed CLI.
- Keep secrets as references, not values. Do not render passwords or keys into
  examples, logs, or committed artifacts.
- Use whitespace control deliberately (`{%-`, `-%}`) and test the exact output;
  blank lines and indentation can affect device parsers and diffs.
- Validate addresses, VLAN IDs, interface names, and enums before rendering.
- Do not put complex business decisions in templates. Compute intent in Python
  or the source model and keep template branches shallow.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define a schema for the YAML variables and identify required fields.
2. Create a small template with deterministic ordering and explicit defaults.
3. Render with `StrictUndefined`, inspect output, and fail on warnings/errors.
4. Test empty lists, optional blocks, multiple records, and invalid values.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```jinja2
{% for server in syslog_servers -%}
logging host {{ server.address }} transport udp port {{ server.port | default(514) }}
{%- endfor %}
```

```python
from jinja2 import Environment, FileSystemLoader, StrictUndefined
env = Environment(loader=FileSystemLoader("templates"), undefined=StrictUndefined,
                  trim_blocks=True, lstrip_blocks=True)
rendered = env.get_template("syslog.j2").render(syslog_servers=data["syslog_servers"])
```

## Validation, Linting & Testing Commands

- Run the bundled renderer against valid and invalid fixtures.
- Compare rendered output with golden files and check for `None`, unresolved
  braces, duplicate commands, or unintended blank lines.
- Run `yamllint` and `python3 scripts/validate_skills.py`.

## References

- [Jinja documentation](https://jinja.palletsprojects.com/en/stable/)
- [Jinja API](https://jinja.palletsprojects.com/en/stable/api/)

## Offline Execution Contract

Render only from local templates and supplied data. If Jinja2 or YAML libraries are unavailable, preserve the input/output contract and do not hand-author a rendered configuration while claiming strict validation.

## Architecture & Technical Design Patterns

Use one environment factory everywhere:

```python
from jinja2 import Environment, FileSystemLoader, StrictUndefined

def environment(path: str) -> Environment:
    return Environment(loader=FileSystemLoader(path), undefined=StrictUndefined,
                       trim_blocks=True, lstrip_blocks=True,
                       keep_trailing_newline=True, autoescape=False)
```

YAML should contain intent such as `interfaces`, `vlans`, `ntp_servers`, and
`syslog_servers`; it should not contain template fragments. Validate enum
values and numeric ranges before rendering. Use `-%}` only where removing the
newline is intentional, render lists in sorted/stable order, and compare the
result to a golden fixture. Search rendered output for unresolved `{{`, `}}`,
`None`, `undefined`, duplicate commands, and secret-looking values before
handing it to a device or downstream tool.
