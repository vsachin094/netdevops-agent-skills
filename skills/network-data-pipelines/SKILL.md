---
name: network-data-pipelines
description: "Build validated Pandas or Polars pipelines with Pydantic schemas to ingest, normalize, join, and audit network datasets such as ARP/MAC tables, BGP RIBs, firewall hits, and IPAM exports. Use this skill when network data must be reconciled at scale into compliance or operational reports."
license: MIT
compatibility: Python 3.10+; Pandas or Polars; Pydantic 2; JSON/CSV/Parquet inputs; pytest optional
---

# Network Data Pipelines (Advanced)

Treat device data as an untrusted, versioned input contract. Validate at the
boundary, normalize identifiers before joining, and make dropped or ambiguous
records visible in the report.

## Core Engineering Capabilities

- Define Pydantic schemas for device, interface, MAC, ARP, BGP, firewall, and
  IPAM records.
- Normalize MAC addresses, interface aliases, IPs, timestamps, device names,
  and VRF identifiers consistently across vendors.
- Join large datasets with Pandas or Polars and emit compliance exceptions,
  lineage metadata, and machine-readable reports.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Validate every source schema before transformation; reject or quarantine
  malformed rows rather than coercing them to null silently.
- Normalize `aabb.ccdd.eeff` and `aa-bb-cc-dd-ee-ff` to one MAC format and
  `Gi0/1`, `Eth1/1`, etc. to a documented interface naming policy.
- Include device, collection time, source, VRF, and parser version in records.
- Make joins explicit and inspect cardinality. A many-to-many join on device
  and MAC is a data-quality incident, not a successful merge.
- Use bounded memory strategies for large exports and never load secrets or
  raw credentials into analytical frames.
- Preserve rejected rows and reasons in a quarantine output.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Inventory each source, schema, identity key, timestamp field, normalization rule, retention requirement, and downstream consumer. Decide how duplicates, stale records, and partial source failures should appear in the output.

### Phase 2 (Implementation)

Generate a staged pipeline that validates at ingestion, normalizes into a stable schema, records provenance, and emits deterministic reports or artifacts. Keep source adapters separate from transformation and presentation.

### Phase 3 (Verification)

Run clean, duplicate, stale, missing-field, malformed, and partial-source fixtures. Compare output hashes or golden records and verify a rerun does not duplicate or reorder records unexpectedly.

1. Inventory sources and define schemas and field lineage.
2. Parse and validate each source independently.
3. Normalize identifiers and timestamps, then profile uniqueness and nulls.
4. Join with explicit keys and cardinality assertions.
5. Produce report, quarantine, metrics, and provenance outputs.

## Production Code / Template Example

### Input / Requirement

Provide source samples, schema and identity keys, transformation rules, expected output, failure policy, and the report or API consumed downstream.

### Output / Generated Code

Return schemas, pipeline stages, normalized fixtures, validation errors, and a sample report with provenance for every material field.


```python
from pydantic import BaseModel, IPvAnyAddress

class ArpRecord(BaseModel):
    device: str
    vrf: str = "global"
    ip: IPvAnyAddress
    mac: str
    interface: str

def normalize_mac(value: str) -> str:
    compact = value.replace(".", "").replace(":", "").replace("-", "").lower()
    if len(compact) != 12 or any(c not in "0123456789abcdef" for c in compact):
        raise ValueError(f"invalid MAC: {value}")
    return ":".join(compact[i:i + 2] for i in range(0, 12, 2))
```

## Validation, Linting & Testing Commands

- Test malformed schemas, duplicate keys, null identifiers, cross-VRF joins,
  timestamp skew, and many-to-many explosions.
- Compare row counts and key cardinality before and after each transformation.
- Emit a data-quality summary with accepted, rejected, duplicate, and joined
  record counts.
- Run `python3 scripts/validate_skills.py` from the repository root.

## References

- [Pydantic documentation](https://docs.pydantic.dev/)
- [Polars documentation](https://docs.pola.rs/)
- [Pandas documentation](https://pandas.pydata.org/docs/)

## Offline Execution Contract

The pipeline must run on local CSV/JSON/Parquet fixtures with schema and cardinality checks. If Pandas/Polars/Pydantic is unavailable, preserve the schema and transformation contract and fail clearly rather than coercing unknown data.

## Architecture & Technical Design Patterns

Use a source adapter per input, a canonical model, and a report adapter. A
canonical network record should carry `device`, `collected_at`, `source`,
`vrf`, and a normalized identifier. Normalize MACs by removing `.`, `:`, and
`-`, lowercasing, validating 12 hex characters, and joining pairs with `:`.
Normalize interfaces with an explicit alias map (`Gi` to
`GigabitEthernet`, `Eth` to the platform's documented form); never guess
ambiguous abbreviations.

Before every join, assert key uniqueness and expected cardinality. For example,
device+VRF+IP should be one-to-zero-or-one in an ARP table, while device+MAC
may be one-to-many. Track `input_rows`, `accepted_rows`, `rejected_rows`,
`duplicate_keys`, and `output_rows`. Quarantine invalid records with the
original row, source, and validation error. Use chunked reads or Polars
lazy execution for large exports and never silently convert parse failures to
nulls.
