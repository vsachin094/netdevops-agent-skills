---
name: ttp-parsers
description: "[Tier: Advanced] Build hierarchical TTP templates that parse nested network configuration and operational output into structured JSON or YAML. Use this skill when records depend on indentation, nested groups, repeated blocks, dynamic paths, or TTP matchers such as IP, PREFIX, MAC, and ignore."
license: MIT
compatibility: Python 3.10+; ttp 0.9+; YAML/JSON; pytest optional
---

# TTP Parsers (Advanced)

Use TTP for hierarchical text where a flat regex or finite table template
would obscure parent-child relationships. Keep the result schema intentional:
TTP's flexible paths are powerful enough to create unstable, hard-to-review
data if group names and list/dictionary choices are left implicit.

## Core Engineering Capabilities

- Parse VRFs, interfaces, BGP address families, route-maps, ACLs, and nested
  configuration blocks into structured results.
- Use `<group>`, match variables, built-in matchers, functions, path formatters,
  dynamic paths, and `ignore` rules for controlled extraction.
- Generate JSON/YAML output for downstream validation, compliance, or template
  rendering while preserving device and section context.
- Use TTP's CLI and API to run one or many fixtures with deterministic output.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Begin with a written output schema. Every group path must map to a deliberate
  object or list, and dynamic keys must come from validated input fields.
- Anchor groups to real hierarchy and indentation. Do not treat whitespace as
  decoration when it carries parent-child meaning.
- Use `IP`, `PREFIX`, `MAC`, and other matchers to reject malformed values;
  do not capture arbitrary `\S+` for fields with a known grammar.
- Keep match functions deterministic and side-effect free. A template must be
  understandable without a hidden global lookup or network call.
- Prevent accidental record merging by closing groups at the right boundary;
  test multiple siblings and repeated parent blocks.
- Use `ignore` narrowly for known banners, prompts, and noise. Do not ignore
  lines that could indicate a changed or unsupported command format.
- Keep vendor/version variants in separate templates or explicit branches and
  document which branch was selected.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Capture representative hierarchical text, section boundaries, repeated records, optional lines, and malformed or truncated input. Define the output nesting and normalization contract before writing groups.

### Phase 2 (Generation)

Build a TTP template with explicit groups, record boundaries, variable names, and output shaping. Keep vendor or command variants separate when a shared template would create ambiguous matches.

### Phase 3 (Self-Verification)

Run the template against complete, empty, multi-section, reordered, and malformed fixtures. Compare full nested structures and verify optional groups do not leak values into the next section.

1. Capture nested fixtures with at least two parent objects and one empty or
   optional child section.
2. Define the target JSON/YAML shape, including whether repeated groups are
   lists and whether keys are static or dynamic.
3. Build the template from the outside in: input, parent group, child group,
   match variables, then functions and output formatting.
4. Run TTP through its API or CLI and inspect the complete result, not a
   hand-picked field.
5. Add fixtures for missing children, reordered siblings, wrapped values,
   duplicate keys, and unexpected syntax.
6. Validate types and domain constraints after parsing. TTP extraction is not
   a substitute for schema validation.
7. Record the template version, TTP version, command, platform, and fixture
   provenance alongside the parser.

## Production Code / Template Example

### Input / Requirement

Provide raw text fixtures, desired nested output, hierarchy rules, supported variants, and the TTP version or consumer integration.

### Output / Generated Code

Return the template, fixture set, expected structured output, variant notes, and tests for section isolation and incomplete records.


### TTP template

```xml
<group name="vrfs*">
vrf definition {{ vrf | _start_ }}
 rd {{ rd | IP }}
 <group name="address_families*">
 address-family {{ af | word }}
  route-target import {{ import_rt | item }}
 </group>
</group>
```

### Structured output shape

```json
{
  "vrfs": [
    {"vrf": "BLUE", "rd": "192.0.2.10", "address_families": [{"af": "ipv4", "import_rt": "65000:10"}]}
  ]
}
```

The exact matcher and group syntax must be checked against the installed TTP
version and fixture behavior; never assume an illustrative template is valid
without executing it.

## Validation, Linting & Testing Commands

- Run the TTP CLI with JSON output for every fixture and compare against
  checked-in expected results.
- Assert that required groups exist, list cardinality is correct, and no
  unexpected top-level keys appear.
- Run unit tests for custom functions and schema validation separately.
- Profile large configurations and avoid unnecessary multi-process parsing
  when deterministic ordering matters.
- Run `python3 scripts/validate_skills.py` from the repository root.

## Authoritative References

- [TTP documentation](https://ttp.readthedocs.io/en/latest/)
- [TTP CLI documentation](https://github.com/dmulyalin/ttp/blob/master/docs/source/CLI%20tool.rst)

## Offline Execution Contract

Use the local TTP package and captured fixtures. If TTP is unavailable, preserve the target schema and provide the template plus fixture-driven pseudocode; do not claim parsed output without executing the parser.

## Architecture & Technical Design Patterns

Design TTP from the output tree inward. A repeated parent is usually a group
with a list path, while a scalar parent is a normal group:

```xml
<group name="interfaces*">
interface {{ name | _start_ }}
 description {{ description | ORPHRASE }}
 <group name="addresses*">
 ip address {{ address | IP }} {{ mask | IP }}
 </group>
</group>
```

Use `IP`, `PREFIX`, `MAC`, and constrained regex matchers for typed values.
Use dynamic paths only when the key is validated and stable; otherwise the
result shape changes when input order changes. Close groups at real hierarchy
boundaries and test two sibling parents, an empty child group, reordered
children, and a malformed value. Use TTP functions only for deterministic
normalization; schema validation still belongs after parsing.
