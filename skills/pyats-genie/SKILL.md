---
name: pyats-genie
description: "[Tier: Expert] Write Cisco Genie MetaParser classes and pyATS AEtest pre/post-maintenance differential tests for structured device state. Use this skill when Cisco parser schemas, testbed-driven device operations, or before/after validation require typed nested data and pyATS integration."
license: MIT
compatibility: Python 3.10+; pyATS and Genie; YAML testbeds; Cisco device access or recorded outputs; pytest optional
---

# pyATS Genie (Expert)

Treat a Genie parser and its AEtest consumer as one contract. The parser
normalizes device output into a schema; the test verifies state and change
impact. Do not confuse successful CLI execution with a valid operational
result.

## Core Engineering Capabilities

- Implement `MetaParser` subclasses with `schema`, `cli()`, and explicit
  handling for supported output variants.
- Use `Any()`, `Optional()`, `Or()`, and nested schemas to validate structure
  without making optional device capabilities mandatory.
- Build pyATS AEtest setup, test, cleanup, and pre/post differential stages.
- Use testbed YAML with encrypted or externally injected credentials and
  device-specific connection settings.
- Return normalized interface, routing, BGP, OSPF, platform, and inventory
  data suitable for assertions and change reports.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Define the schema before the parser body. Required fields must be required;
  optional fields must reflect actual platform behavior, not parser laziness.
- Parse raw output fixtures in unit tests before connecting to a device. Keep
  fixtures sanitized and version-labelled.
- Do not swallow parser exceptions or return a partial success dictionary when
  a mandatory section is malformed. Include the command and device context in
  diagnostics without exposing credentials.
- Keep device connection and parsing concerns separate. A parser should be
  deterministic for a captured output string.
- Use testbed credentials from environment, vault, or pyATS-supported secure
  mechanisms; never commit cleartext passwords or private keys.
- For maintenance tests, capture a baseline, apply the authorized change,
  collect the same state, compare semantically, and assert the intended delta.
  Do not compare timestamps, counters, or other volatile fields blindly.
- Ensure cleanup restores or releases test resources even when a test fails.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Identify the command, platform/OS release, expected schema, and whether the
   parser is for a local project or intended for upstream contribution.
2. Collect sanitized raw outputs for healthy, degraded, empty, and variant
   states. Define the canonical dictionary shape.
3. Implement the `MetaParser` schema and `cli()` parser with narrow regex or
   helper functions. Validate the returned object against the schema.
4. Add unit tests with raw fixtures and exact expected dictionaries. Include
   malformed and missing-section cases.
5. Build AEtest stages around the parser: baseline, action, post-check,
   differential assertions, and cleanup/rollback.
6. Run offline parser tests first, then a lab testbed. Gate production use on
   a reviewed testbed, explicit change approval, and a rollback path.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
from genie.metaparser import MetaParser
from genie.metaparser.util.schemaengine import Any, Optional

class ShowPeerStateSchema(MetaParser):
    schema = {
        "neighbors": {
            Any(): {
                "state": str,
                Optional("remote_as"): int,
            }
        }
    }

    def cli(self, output: str | None = None) -> dict:
        output = output if output is not None else self.device.execute("show peer state")
        result = {"neighbors": {}}
        # Parse only the documented command format; raise on malformed records.
        return self.validate(result)
```

For a real parser, replace the illustrative body with fixture-driven parsing
and add a schema test. A parser that returns an empty dictionary to avoid a
schema error is not production-safe.

## Validation, Linting & Testing Commands

- Run parser unit tests against sanitized raw fixtures and schema validation.
- Run `pyats run job` or the project’s AEtest entrypoint in a lab testbed.
- Assert pre/post state using semantic fields and exclude documented volatile
  values.
- Check testbed files for secrets and validate connection aliases before use.
- Run `python3 scripts/validate_skills.py` from the repository root.

## Authoritative References

- [Cisco Genie MetaParser documentation](https://developer.cisco.com/docs/genie-metaparser/)
- [Cisco pyATS documentation](https://developer.cisco.com/docs/pyats/)
- [CiscoTestAutomation Genie parser repository](https://github.com/CiscoTestAutomation/genieparser)
- [pyATS Getting Started](https://devnet-pubhub-site.s3.amazonaws.com/media/pyats/docs/getting_started/index.html)

## Offline Execution Contract

Run MetaParser tests against local sanitized output fixtures without a device. If pyATS/Genie or a testbed is unavailable, validate schema and parser structure with standard Python and mark live-device behavior as pending.

## Architecture & Technical Design Patterns

A Genie parser has three contracts: command identity, schema, and returned
dictionary. Define the schema first, then parse each record into the exact
nested keys. Use `Any()` for dynamic identifiers and `Optional()` only for a
field genuinely absent on supported platforms. A parser should accept an
`output` argument for fixture tests and call `self.device.execute()` only when
no output is supplied.

For differential tests, normalize volatile fields before comparison: uptime,
timestamps, counters, software-generated IDs, and session ages are not
configuration intent. Compare stable sets such as interface admin/oper state,
neighbor identity/state, route prefixes, and policy names. A testbed should
declare `devices`, `os`, `type`, connection alias, and credential references;
credentials must be injected or encrypted. When a schema error occurs, fail
with device, command, parser version, and fixture name—never return `{}`.
