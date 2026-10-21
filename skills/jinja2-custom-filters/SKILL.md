---
name: jinja2-custom-filters
description: "[Tier: Advanced] Write reusable typed Jinja2 macros and deterministic Python filters for IP math, BGP peer derivation, interface range compression, and MAC formatting. Use this skill when repeated network transformations belong in tested reusable helpers rather than inline template logic."
license: MIT
compatibility: Python 3.10+; Jinja2; Python ipaddress; pytest; optional type checker
---

# Jinja2 Custom Filters (Advanced)

Custom filters are part of the rendering API. Keep them pure, typed,
deterministic, and independently tested so a formatting helper cannot silently
change network intent.

## Core Engineering Capabilities

- Implement filters for CIDR normalization, host calculation, BGP peer data,
  interface range compression, MAC formatting, and safe quoting.
- Package filters as a reusable module and register them explicitly with the
  Jinja environment.
- Use macros for presentation and Python filters for domain logic that deserves
  unit tests and type validation.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Keep filter functions side-effect free: no network calls, filesystem writes,
  global mutation, or time-dependent output.
- Type-check inputs and raise actionable errors for malformed IPs, VLANs,
  MACs, interfaces, or ASN values. Do not return an empty string on failure.
- Avoid filters that mutate the source object or rely on dictionary ordering
  unless ordering is an explicit contract.
- Register only the filters required by the environment and document output
  type, normalization, and failure behavior.
- Test IPv4, IPv6, boundary prefixes, empty input, duplicate interfaces, and
  invalid values.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

List each filter or macro's input types, output contract, null behavior, exception policy, and the templates that consume it. Identify whether a filter must preserve order, formatting, or vendor-specific aliases.

### Phase 2 (Generation)

Implement small pure filters with type checks, useful error messages, and no hidden I/O. Register them explicitly and document examples that match the actual return type consumed by Jinja.

### Phase 3 (Self-Verification)

Run unit tests for normal, boundary, null, invalid-type, and idempotent cases, then render a fixture through Jinja StrictUndefined. Confirm filter failures identify the input and filter name.

1. Identify repeated transformation and decide whether it belongs in a macro,
   filter, or pre-render model transformation.
2. Define input/output types and implement a pure Python function.
3. Add direct unit tests, register the filter, and add rendered golden tests.
4. Version the filter behavior because changing it can change device config.

## Production Code / Template Example

### Input / Requirement

Provide filter signatures, sample inputs and expected outputs, registration mechanism, supported Python/Jinja versions, and the templates that use the filters.

### Output / Generated Code

Return the filter module, registration code, tests, and a rendered example showing the filter in its real template context.


```python
import ipaddress

def network_address(value: str) -> str:
    try:
        return str(ipaddress.ip_network(value, strict=False).network_address)
    except ValueError as exc:
        raise ValueError(f"invalid network {value!r}") from exc

env.filters["network_address"] = network_address
```

```jinja2
neighbor {{ peer.address }} remote-as {{ peer.asn }}
description {{ peer.description | quote_cli }}
```

## Validation, Linting & Testing Commands

- Run unit tests independently of Jinja and golden rendering tests through the
  registered environment.
- Run type checking and linting adopted by the repository.
- Confirm filters cannot emit secrets or nondeterministic values.
- Run `python3 scripts/validate_skills.py`.

## References

- [Jinja custom filters](https://jinja.palletsprojects.com/en/stable/api/#custom-filters)
- [Python `ipaddress`](https://docs.python.org/3/library/ipaddress.html)

## Offline Execution Contract

Custom filters must be testable as pure local Python functions. Without Jinja2, run direct unit tests and emit the filter module; do not claim rendered output was validated.

## Architecture & Technical Design Patterns

Prefer a Python filter when the operation has domain semantics or needs
validation; prefer a Jinja macro when it only controls presentation. A filter
should have a narrow signature such as `format_mac(value: str) -> str` or
`subnet_hosts(prefix: str, policy: str = "conventional") -> int`. Raise
`ValueError` with the input and expected format on invalid data.

Register filters explicitly:

```python
env.filters.update({"format_mac": format_mac, "network_address": network_address})
```

Test direct function behavior first, then a rendered template. Include IPv4
and IPv6, prefix boundaries, empty lists, duplicate interfaces, invalid MACs,
and deterministic ordering. Never let a filter read environment secrets,
perform I/O, depend on current time, or mutate the model passed by the caller.
