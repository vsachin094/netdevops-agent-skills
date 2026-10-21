---
name: ntc-textfsm
description: "[Tier: Intermediate] Author tested Google TextFSM templates and NTC-Templates-compatible fixtures for semi-structured network CLI output used by Netmiko, Scrapli, and Ansible cli_parse. Use this skill when output has repeatable line-oriented states, records, and continuation lines that exceed a safe single-regex parser."
license: MIT
compatibility: Python 3.10+; textfsm; optional ntc-templates, Netmiko, Scrapli, Ansible, pytest, and yamllint
---

# NTC TextFSM (Intermediate)

Use TextFSM as an explicit line-oriented state machine. A template is a
contract between one command's raw output and a tabular record schema; it is
not a generic parser that should be stretched across unrelated vendors or
commands.

## Core Engineering Capabilities

- Define `Value` fields with `Filldown`, `Key`, `Required`, and `List` options.
- Model headers, repeated records, wrapped descriptions, nested sections, and
  EOF behavior with explicit `Start`, record, and terminal states.
- Produce NTC-Templates-compatible template names, index entries, raw fixtures,
  expected YAML, and regression coverage.
- Integrate with Netmiko `use_textfsm=True`, Scrapli response parsing, and
  Ansible `ansible.utils.cli_parse` without changing the output contract.
- Detect malformed templates, missing required values, duplicate records, and
  state-machine loops before deployment.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Put all `Value` definitions before states and define `Start`; use the exact
  syntax supported by the installed TextFSM version.
- Use uppercase capture names in NTC-style templates and lowercase output keys
  in expected dictionaries, matching the project conventions.
- Mark identity fields `Key` only when they uniquely identify a record. Mark
  fields `Required` when a record without them is invalid; do not use
  `Filldown` to conceal missing data.
- Use `Filldown` only for context that legitimately applies to following
  records. Clear context at the correct state boundary so one chassis, VRF,
  or interface cannot leak into the next section.
- Use explicit `Record` actions and state transitions for wrapped lines. Every
  rule must either consume the line safely, transition intentionally, or allow
  a known ignorable line; avoid catch-all transitions that create loops.
- Preserve raw fixtures from multiple software versions and states. Never
  use production secrets, public IPs, or unredacted device output in tests.
- Keep parsing separate from normalization. Convert numbers, booleans, and
  interface aliases after TextFSM returns records.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Capture raw command output from each supported OS and release, including headers, empty output, wrapped lines, and malformed records. Define the record schema before choosing Value options or state transitions.

### Phase 2 (Generation)

Write the smallest TextFSM state machine that expresses record boundaries, Filldown context, required fields, and EOF behavior. Keep parsing separate from normalization and match NTC-Templates naming and index conventions.

### Phase 3 (Self-Verification)

Run TextFSM directly against every fixture and compare complete dictionaries. Add negative cases for changed headers, missing keys, truncated output, and context leakage before testing Netmiko, Scrapli, or Ansible integration.

1. Capture representative raw output, including empty, partial, paginated, and
   multi-record cases. Identify record boundaries and context fields.
2. Define the output schema and decide which fields are `Key`, `Required`,
   `Filldown`, or `List` before writing regex.
3. Write the smallest template: values, `Start`, record state(s), and explicit
   transitions. Prefer anchored rules and bounded whitespace.
4. Run TextFSM directly against fixtures. Compare parsed records with expected
   YAML/JSON, not merely the record count.
5. Add negative fixtures for truncated output, changed headers, missing keys,
   wrapped lines, and unexpected state transitions.
6. Check compatibility with the consumer and index naming conventions. A
   template that parses locally but is not discoverable by Netmiko is incomplete.
7. Document supported vendor OS and command variants, ignored lines, and
   migration criteria for TTP, Genie, or a structured API.

## Production Code / Template Example

### Input / Requirement

Provide raw fixtures, expected records, command and platform names, supported software variants, and the consuming library or index requirements.

### Output / Generated Code

Return the template, index entry where applicable, raw and expected fixtures, integration example, and parser/test output.


### Template

```text
Value Required INTERFACE (\S+)
Value STATUS (up|down)
Value PROTOCOL (up|down)

Start
  ^${INTERFACE}\s+is\s+${STATUS}, line protocol is ${PROTOCOL} -> Record
  ^\s*$$
```

### Fixture and expected record

```text
GigabitEthernet0/1 is up, line protocol is up
GigabitEthernet0/2 is down, line protocol is down
```

```yaml
parsed_sample:
  - interface: GigabitEthernet0/1
    status: up
    protocol: up
  - interface: GigabitEthernet0/2
    status: down
    protocol: down
```

## Validation, Linting & Testing Commands

- Run the template parser against every raw fixture and compare complete
  dictionaries.
- Use the TextFSM parser's own errors as CI failures; never suppress template
  parse exceptions.
- Run `yamllint` on expected YAML and project linting on template/index files.
- Verify no record has missing `Required` fields and no context field leaks
  between sections.
- Run `python3 scripts/validate_skills.py` from the repository root.

## Authoritative References

- [Google TextFSM](https://github.com/google/textfsm)
- [TextFSM state and Value documentation](https://github.com/google/textfsm/wiki/TextFSM)
- [NTC-Templates parser development guide](https://github.com/networktocode/ntc-templates/blob/master/docs/dev/dev_parser.md)

## Offline Execution Contract

Use installed TextFSM and local raw/expected fixtures. If ntc-templates, Netmiko, or a device is unavailable, validate the template directly and return the standard records; never infer an undocumented vendor variant.

## Architecture & Technical Design Patterns

A production template follows this order: contiguous `Value` definitions,
blank line, mandatory `Start` state, then named states. Use `Required` for
record identity fields, `Filldown` for section context, `List` for repeated
values, and `Key` only for a true unique key. Example:

```text
Value Required INTERFACE (\S+)
Value STATUS (up|down)
Value List ADDRESS (\S+)

Start
  ^${INTERFACE} is ${STATUS} -> Record
  ^\s+Internet address is ${ADDRESS}
```

State transitions must consume the line that causes them. For wrapped records,
transition from a header to a record state, collect continuation lines there,
and transition back only at the next record/header boundary. Use `-> Record`
after the final mandatory field, not on a generic catch-all line. An explicit
empty `EOF` state suppresses accidental partial records; otherwise TextFSM
records the current row at EOF.

For NTC-style contributions, name templates as
`vendor_os_command_with_underscores.textfsm`, keep capture names uppercase,
output keys lowercase, and store raw text plus expected YAML beside the
template. Test at least two versions and an incomplete record.
