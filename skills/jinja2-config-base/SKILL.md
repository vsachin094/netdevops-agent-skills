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

Identify the vendor OS, command/configuration mode, data schema, required defaults, whitespace rules, and output artifact. Separate values that belong in YAML or JSON from logic that belongs in the template.

### Phase 2 (Generation)

Generate a strict Jinja environment with explicit undefined-variable behavior, deterministic ordering, reusable macros, and vendor-safe whitespace. Keep templates free of credentials and avoid emitting commands for absent data.

### Phase 3 (Self-Verification)

Render known-good and invalid data fixtures, compare golden output, run syntax checks where available, and test empty lists, missing required fields, and repeated rendering for stability.

1. Define a schema for the YAML variables and identify required fields.
2. Create a small template with deterministic ordering and explicit defaults.
3. Render with `StrictUndefined`, inspect output, and fail on warnings/errors.
4. Test empty lists, optional blocks, multiple records, and invalid values.

## Production Code / Template Example

### Input / Requirement

Provide the structured intent data, target vendor/version, expected rendered configuration, required fields, and the command or parser used to validate the output.

### Output / Generated Code

Return the template, data schema or sample input, rendered golden output, and tests for valid, incomplete, empty, and repeated input.


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
