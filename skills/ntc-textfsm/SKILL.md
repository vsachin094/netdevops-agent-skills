---
name: ntc-textfsm
description: "[Tier: Intermediate] Author tested Google TextFSM templates and NTC-Templates-compatible fixtures for semi-structured network CLI output used by Netmiko, Scrapli, and Ansible cli_parse. Use this skill when output has repeatable line-oriented states, records, and continuation lines that exceed a safe single-regex parser."
license: MIT
compatibility: Python 3.10+; textfsm 1.1+; optional ntc-templates 2.4+, Netmiko 4+, Scrapli 2023+, Ansible Core 2.15+, pytest, yamllint
---

# NTC TextFSM (Intermediate)

Use TextFSM as an explicit line-oriented state machine. A template is a contract between one command's raw output and a tabular record schema; it is not a generic parser that should be stretched across unrelated vendors or commands.

## Core Engineering Capabilities

- Define `Value` fields with `Filldown`, `Key`, `Required`, and `List` options.
- Model headers, repeated records, wrapped descriptions, nested sections, and EOF behavior with explicit `Start`, record, and terminal states.
- Produce NTC-Templates-compatible template names, index entries, raw fixtures, expected YAML, and regression coverage.
- Integrate with Netmiko `use_textfsm=True`, Scrapli response parsing, and Ansible `ansible.utils.cli_parse` without changing the output contract.
- Detect malformed templates, missing required values, duplicate records, and state-machine loops before deployment.
- Handle vendor version drift: template per OS major version when output structure changes (e.g., IOS 15.x vs 17.x, NX-OS 7.x vs 9.x).

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- **Put all `Value` definitions before states and define `Start`**; use the exact syntax supported by the installed TextFSM version.
- **Use uppercase capture names in NTC-style templates** and lowercase output keys in expected dictionaries, matching the project conventions.
- **Mark identity fields `Key` only when they uniquely identify a record.** Mark fields `Required` when a record without them is invalid; do not use `Filldown` to conceal missing data.
- **Use `Filldown` only for context that legitimately applies to following records.** Clear context at the correct state boundary so one chassis, VRF, or interface cannot leak into the next section. Test Filldown leakage by concatenating multi-device output.
- **Use explicit `Record` actions and state transitions for wrapped lines.** Every rule must either consume the line safely, transition intentionally, or allow a known ignorable line; avoid catch-all transitions that create loops.
- **Preserve raw fixtures from multiple software versions and states.** Never use production secrets, public IPs, or unredacted device output in tests.
- **Keep parsing separate from normalization.** Convert numbers, booleans, and interface aliases after TextFSM returns records.
- **Migration criteria:** When a template exceeds ~80 lines, has >5 states, or requires nested context that TextFSM cannot express cleanly, migrate to TTP or pyATS/Genie.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Capture raw command output from each supported OS and release, including headers, empty output, wrapped lines, and malformed records. Define the record schema before choosing Value options or state transitions. Identify vendor, command, OS versions, and output variants.

### Phase 2 (Implementation)

Write the smallest TextFSM state machine that expresses record boundaries, Filldown context, required fields, and EOF behavior. Keep parsing separate from normalization and match NTC-Templates naming and index conventions.

1. Capture representative raw output, including empty, partial, paginated, and multi-record cases. Identify record boundaries and context fields.
2. Define the output schema and decide which fields are `Key`, `Required`, `Filldown`, or `List` before writing regex.
3. Write the smallest template: values, `Start`, record state(s), and explicit transitions. Prefer anchored rules and bounded whitespace.
4. Add version-specific templates when output structure differs (e.g., `cisco_ios_show_ip_bgp_summary.textfsm` vs `cisco_ios_17_show_ip_bgp_summary.textfsm`).
5. Create index entry in `index` file mapping command + platform + version to template.

### Phase 3 (Verification)

Run TextFSM directly against every fixture and compare complete dictionaries. Add negative cases for changed headers, missing keys, truncated output, and context leakage before testing Netmiko, Scrapli, or Ansible integration.

1. Run TextFSM directly against fixtures. Compare parsed records with expected YAML/JSON, not merely the record count.
2. Add negative fixtures for truncated output, changed headers, missing keys, wrapped lines, and unexpected state transitions.
3. **Filldown leakage test:** Concatenate raw output from 3+ devices; verify no context (VRF, chassis, interface) leaks across device boundaries.
4. Check compatibility with the consumer and index naming conventions. A template that parses locally but is not discoverable by Netmiko is incomplete.
5. Document supported vendor OS and command variants, ignored lines, and migration criteria for TTP, Genie, or a structured API.

## Production Code / Template Example

### Input / Requirement

Provide raw fixtures, expected records, command and platform names, supported software variants, and the consuming library or index requirements.

### Output / Generated Code

Return the template, index entry where applicable, raw and expected fixtures, integration example, and parser/test output.

### Template (IOS 15.x BGP Summary)

```text
Value Required VRF (\S+)
Value Required NEIGHBOR (\S+)
Value REQUIRED AS (\d+)
Value STATE (Estab|Idle|Active|OpenSent|OpenConfirm)
Value PFX_RCVD (\d+)

Start
  ^BGP router identifier\s+\S+, local AS number\s+\d+ -> Continue
  ^VRF\s+${VRF} -> Continue.Record
  ^${NEIGHBOR}\s+${AS}\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+${STATE}\s+${PFX_RCVD} -> Record
  ^\s*$$ -> Start
```

### Template (IOS 17.x BGP Summary - version drift)

```text
Value Required VRF (\S+)
Value Required NEIGHBOR (\S+)
Value REQUIRED AS (\d+)
Value STATE (Established|Idle|Active|OpenSent|OpenConfirm)
Value PFX_RCVD (\d+)

Start
  ^BGP router identifier\s+\S+, local AS number\s+\d+ -> Continue
  ^VRF\s+${VRF} -> Continue.Record
  ^${NEIGHBOR}\s+${AS}\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+${STATE}\s+${PFX_RCVD} -> Record
  ^\s*$$ -> Start
```

### Fixture and expected record

```text
BGP router identifier 192.0.2.1, local AS number 65001
VRF default
192.0.2.2     65000  100  100   0  0  0  0  0  0  00:05:23 Estab  1250
192.0.2.3     65000  100  100   0  0  0  0  0  0  00:05:23 Estab  1250
```

```yaml
parsed_sample:
  - vrf: default
    neighbor: 192.0.2.2
    as: 65000
    state: Estab
    pfx_rcvd: 1250
  - vrf: default
    neighbor: 192.0.2.3
    as: 65000
    state: Estab
    pfx_rcvd: 1250
```

### Filldown leakage test fixture

```text
# Device 1 output
BGP router identifier 192.0.2.1, local AS number 65001
VRF default
192.0.2.2     65000  ... Estab  1250

# Device 2 output (concatenated)
BGP router identifier 192.0.2.10, local AS number 65002
VRF management
192.0.2.11    65001  ... Estab  50
```

Expected: Device 2 records have `vrf: management`, not `vrf: default`.

## Validation, Linting & Testing Commands

- Run the template parser against every raw fixture and compare complete dictionaries: `python -m textfsm template.textfsm < fixture.txt`
- Use the TextFSM parser's own errors as CI failures; never suppress template parse exceptions.
- Run `yamllint` on expected YAML and project linting on template/index files.
- Verify no record has missing `Required` fields and no context field leaks between sections.
- **Version drift test:** Run each version-specific template against its fixture and against other versions' fixtures; verify graceful failure (no records) not wrong records.
- **Filldown leakage test:** Concatenate 3+ device outputs; run template; assert no cross-device context leakage.
- Run `python3 scripts/validate_skills.py` from the repository root.

## Authoritative References

- [Google TextFSM](https://github.com/google/textfsm)
- [TextFSM state and Value documentation](https://github.com/google/textfsm/wiki/TextFSM)
- [NTC-Templates parser development guide](https://github.com/networktocode/ntc-templates/blob/master/docs/dev/dev_parser.md)

## Offline Execution Contract

Use installed TextFSM and local raw/expected fixtures. If ntc-templates, Netmiko, or a device is unavailable, validate the template directly and return the standard records; never infer an undocumented vendor variant.

## Architecture & Technical Design Patterns

A production template follows this order: contiguous `Value` definitions, blank line, mandatory `Start` state, then named states. Use `Required` for record identity fields, `Filldown` for section context, `List` for repeated values, and `Key` only for a true unique key.

```text
Value Required INTERFACE (\S+)
Value STATUS (up|down)
Value List ADDRESS (\S+)

Start
  ^${INTERFACE} is ${STATUS} -> Record
  ^\s+Internet address is ${ADDRESS}
```
```python
# Parse CLI output with TextFSM and validate expected records.
# Values are illustrative; replace template path, raw output, and expected keys.
import textfsm
import yaml
from pathlib import Path

def parse_with_textfsm(template_path: Path, raw_output: str) -> list[dict]:
    with template_path.open() as f:
        fsm = textfsm.TextFSM(f)
    raw_records = fsm.ParseText(raw_output)
    headers = [h.lower() for h in fsm.header]
    return [dict(zip(headers, record)) for record in raw_records]

# Example usage (illustrative; requires textfsm 1.1+ and a valid .textfsm file)
# template = Path("templates/cisco_ios_show_ip_int_brief.textfsm")
# raw = Path("fixtures/show_ip_int_brief.txt").read_text()
# records = parse_with_textfsm(template, raw)
# for rec in records:
#     assert rec["status"] in ("up", "down"), f"Unexpected status: {rec}"
```


CLI output can change across device releases, even when the command is
unchanged. Do not assume a template is compatible across a vendor's versions:
retain sanitized raw fixtures from each supported release, test the template
against those fixtures, and document the exact versions exercised. The
NTC-Templates index and current upstream template are useful references, but
must not replace tests against the output your automation will parse. Confirm
the supported TextFSM syntax against the installed TextFSM version.

## Related Skills

- [ttp-parsers](../ttp-parsers/SKILL.md) — Hierarchical parsing when TextFSM state machine becomes unwieldy
- [pyats-genie](../pyats-genie/SKILL.md) — Cisco Genie parsers for structured output
- [netmiko-core](../netmiko-core/SKILL.md) — Consumer of TextFSM via `use_textfsm=True`
- [cli-regex](../cli-regex/SKILL.md) — Simpler regex parsing for stable output formats
- [network-protocols-as-code](../network-protocols-as-code/SKILL.md) — Intent-driven rendering avoids parsing entirely