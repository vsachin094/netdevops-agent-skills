---
name: cli-regex
description: "[Tier: Basic] Write pure Python regular-expression parsers that convert raw network CLI output and syslog text into structured dictionaries or JSON. Use this skill when a command has stable textual structure and a small, testable parser is preferable to TextFSM, TTP, Genie, or a vendor API."
license: MIT
compatibility: Python 3.10+ standard library; pytest optional; raw command output supplied as text or fixture files
---

# CLI Regex (Basic)

Build a small parser that is explicit about the input dialect, output schema,
and failure behavior. Regular expressions are appropriate for stable,
bounded output formats; they are not a substitute for a stateful parser when
the input contains nested configuration, arbitrary wrapping, or significant
context across lines.

## Core Engineering Capabilities

- Parse operational output such as interface summaries, BGP summaries, LLDP
  neighbors, optical DOM values, ARP/MAC records, and syslog messages.
- Normalize terminal artifacts including ANSI color/control sequences,
  carriage returns, pager prompts such as `--More--`, and device prompts.
- Extract typed fields with named capture groups: `(?P<field_name>...)`.
- Handle repeated records with `Pattern.finditer`, optional columns, and
  controlled whitespace without relying on fixed character offsets.
- Return stable dictionaries or JSON records with documented missing-value
  semantics, units, and normalization rules.
- Supply positive, negative, boundary, and regression fixtures and expose
  unmatched lines rather than silently dropping data.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

1. **Use raw Python patterns.** Write regex literals as raw strings (`r"..."`)
   so Python string escaping does not corrupt regex escapes.
2. **Name every extracted field.** Use named groups for data consumed by the
   application. Use non-capturing groups `(?:...)` for structural grouping.
   Do not build production output around numeric group positions.
3. **Normalize before matching.** Strip ANSI escape sequences, pager markers,
   trailing prompts, and line-ending differences in one named function. Keep
   the raw input available for troubleshooting; do not mutate it destructively
   before it can be logged or stored under the repository's data policy.
4. **Anchor records deliberately.** Use `^`/`$` with `re.MULTILINE` when a
   record is line-oriented. Avoid `.*` across lines and avoid greedy captures
   for fields with a known delimiter; these patterns cause cross-record
   matches and catastrophic backtracking.
5. **Choose the right operation.** Use `fullmatch` for a complete line,
   `match` for a known line prefix, `search` for a marker anywhere, and
   `finditer` for repeated records. Do not call `findall` when match spans or
   named-group diagnostics are needed.
6. **Type after extraction.** Convert integers, floats, booleans, timestamps,
   IP addresses, and interface names in a separate normalization function.
   Preserve the original text when a conversion fails and report the error.
7. **Fail visibly.** A parser must expose unmatched non-empty candidate lines,
   duplicate identifiers, missing mandatory fields, and unexpected headers.
   Returning an empty list with exit code zero is not a valid success case.
8. **Keep scope bounded.** Set a maximum input size, avoid nested ambiguous
   quantifiers, and do not run a complex regex against untrusted, unlimited
   data without a timeout-capable regex engine or other containment.
9. **Protect sensitive output.** Fixtures must use documentation addresses and
   fake credentials. Do not commit production configs, SNMP strings, keys, or
   raw device logs containing secrets.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. **Characterize the command.** Capture representative output from at least
   two software versions or operational states when possible. Identify the
   header, record boundary, continuation/wrapped lines, pagination behavior,
   and prompt.
2. **Define the output contract.** Specify record keys, required versus
   optional values, types, units, normalized interface names, and behavior for
   missing or unsupported fields.
3. **Write normalization first.** Implement `normalize_cli(text) -> str` and
   unit-test ANSI, pager, CRLF, prompt, and blank-line handling independently.
4. **Write the smallest anchored pattern.** Start with one valid record and
   named groups. Add optional branches only when fixtures demonstrate the
   variation. Do not guess vendor syntax from a screenshot or memory.
5. **Parse and normalize.** Compile the pattern once, iterate records, convert
   values, and construct the documented schema. Keep matching separate from
   business validation.
6. **Test failure behavior.** Include missing fields, malformed values,
   wrapped descriptions, empty output, command errors, pager artifacts, and
   a line that must remain unmatched.
7. **Run the deterministic harness.** Use the bundled `test_regex.py` to
   compare extracted records with expected JSON:

   ```bash
   python3 skills/cli-regex/scripts/test_regex.py \
     --pattern '^(?P<name>\S+)\s+(?P<state>up|down)$' \
     --input fixture.txt \
     --expected expected.json
   ```

8. **Document limits.** State supported vendors/releases, known output
   variants, fields intentionally ignored, and when to migrate to TextFSM,
   TTP, Genie, or a structured API.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


### Input

```text
GigabitEthernet0/1 is up, line protocol is up
  Hardware is ISR, address is 0050.56aa.bbcc
  Description: WAN edge
  Internet address is 192.0.2.2/31
```

### Parser

```python
import re

INTERFACE = re.compile(
    r"^(?P<name>\S+) is (?P<admin>up|down), "
    r"line protocol is (?P<oper>up|down)$",
    re.MULTILINE,
)

def parse_interfaces(text: str) -> list[dict[str, str]]:
    return [match.groupdict() for match in INTERFACE.finditer(normalize_cli(text))]
```

### Output

```json
[{"name": "GigabitEthernet0/1", "admin": "up", "oper": "up"}]
```

If the description and address are required output fields, do not add a
second unconstrained `.*` to this pattern. Define a line-oriented state
machine in the parser or move the use case to TextFSM/TTP when continuation
lines are a core part of the format.

### Normalization example

```python
ANSI = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
PAGER = re.compile(r"(?:\x08+|--More--|\x1b\[K)")

def normalize_cli(text: str) -> str:
    text = ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    text = PAGER.sub("", text)
    return "\n".join(line.rstrip() for line in text.splitlines())
```

## Validation, Linting & Testing Commands

- Run `python3 skills/cli-regex/scripts/test_regex.py` with positive and
  negative fixtures.
- Run `python3 -m compileall` or `python3 -m py_compile` on generated parser
  modules.
- Add pytest cases for every supported output variant and every required
  field. Assert both parsed values and unmatched-line behavior.
- Inspect `pattern.groupindex` and ensure all application fields use named
  groups. Use `re.DEBUG` during development when a pattern is unexpectedly
  slow or ambiguous.
- Test input size and runtime against a worst-case fixture. Avoid nested
  greedy quantifiers and catastrophic backtracking.
- Run `python3 scripts/validate_skills.py` from the repository root.
- Re-evaluate the parser choice when output becomes nested, multiline, highly
  version-dependent, or available through a structured API.

## Authoritative References

- [Python `re` documentation](https://docs.python.org/3/library/re.html)
- [Python Regular Expression HOWTO](https://docs.python.org/3/howto/regex.html)
- [Python text processing documentation](https://docs.python.org/3/library/text.html)

## Offline Execution Contract

The parser workflow is fully local with Python `re` and fixtures. When no live output or documentation is available, require supplied samples, preserve unmatched lines, and state the exact output variants that remain unverified.

## Architecture & Technical Design Patterns

Use a three-layer parser: normalization, extraction, and typing. A practical
normalizer is:

```python
ANSI = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
def normalize(text: str) -> str:
    text = ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?:--More--|\x08+)", "", text)
    return "\n".join(line.rstrip() for line in text.splitlines())
```

For a repeated line-oriented record, compile once with `re.MULTILINE` and use
`finditer()`:

```python
RX = re.compile(
    r"^(?P<interface>\S+)\s+(?P<status>up|down)\s+"
    r"(?P<protocol>up|down)\s+(?P<address>\S+)$", re.M)
records = [m.groupdict() for m in RX.finditer(normalize(raw))]
```

Reject a parser design when the record needs parent context, arbitrary
continuation lines, nested configuration, or vendor-specific state. Use
TextFSM/TTP/Genie instead. For metrics, convert values after matching:
`int`, `float`, `ipaddress.ip_interface`, and explicit boolean maps. Return a
`ParseResult(records, unmatched_lines, warnings)` shape when silent data loss
would be dangerous.
