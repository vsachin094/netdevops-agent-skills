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

**State transitions must consume the line that causes them.** For wrapped records, transition from a header to a record state, collect continuation lines there, and transition back only at the next record/header boundary. Use `-> Record` after the final mandatory field, not on a generic catch-all line. An explicit empty `EOF` state suppresses accidental partial records; otherwise TextFSM records the current row at EOF.

**Version handling:** When vendor output changes across major versions (IOS 15→17, NX-OS 7→9, Junos 18→21), create separate templates with version in filename. Use a dispatcher in the consumer (Netmiko/Scrapli) that selects template by `device.version`.

**NTC-style contribution:** Name templates as `vendor_os_command_with_underscores.textfsm`, keep capture names uppercase, output keys lowercase, and store raw text plus expected YAML beside the template. Test at least two versions and an incomplete record.

**Migration to TTP/Genie triggers:**
- Template > 80 lines
- > 5 states
- Need to capture nested configuration blocks (not operational output)
- Vendor adds structured API (NETCONF/RESTCONF/gNMI) for the same data
- Template requires context that spans non-adjacent lines (TextFSM is line-oriented)

## Vendor Version Compatibility

| Vendor | Command | Version | Template File | Notes |
|--------|---------|---------|---------------|-------|
| Cisco IOS | show ip bgp summary | 15.x | cisco_ios_show_ip_bgp_summary.textfsm | Legacy format |
| Cisco IOS | show ip bgp summary | 17.x | cisco_ios_17_show_ip_bgp_summary.textfsm | "Established" vs "Estab" |
| Cisco NX-OS | show ip bgp summary | 7.x | cisco_nxos_show_ip_bgp_summary.textfsm | Different column layout |
| Cisco NX-OS | show ip bgp summary | 9.x | cisco_nxos_9_show_ip_bgp_summary.textfsm | Updated headers |
| Juniper Junos | show bgp summary | 18.x | juniper_junos_show_bgp_summary.textfsm | Different output format |
| Juniper Junos | show bgp summary | 21.x | juniper_junos_21_show_bgp_summary.textfsm | XML-like formatting |
| Arista EOS | show ip bgp summary | 4.25+ | arista_eos_show_ip_bgp_summary.textfsm | Consistent across versions |

**Notes:**
- Always test against at least two major versions per vendor
- NTC-Templates index maps command+platform+version to template
- TextFSM 1.1+ required for `Key` and `Filldown` behavior

## Related Skills

- [ttp-parsers](ttp-parsers.md) — Hierarchical parsing when TextFSM state machine becomes unwieldy
- [pyats-genie](pyats-genie.md) — Cisco Genie parsers for structured output
- [netmiko-core](netmiko-core.md) — Consumer of TextFSM via `use_textfsm=True`
- [cli-regex](cli-regex.md) — Simpler regex parsing for stable output formats
- [network-protocols-as-code](network-protocols-as-code.md) — Intent-driven rendering avoids parsing entirely