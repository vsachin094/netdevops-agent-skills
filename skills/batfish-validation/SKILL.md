---
name: batfish-validation
description: "[Tier: Expert] Write pybatfish validation for routing, ACL reachability, BGP session compatibility, undefined references, differential behavior, and forwarding loops before network changes reach production. Use this skill when offline mathematical analysis of a snapshot can provide stronger evidence than syntax checks alone."
license: MIT
compatibility: Batfish service; pybatfish; sanitized vendor configs and supplemental topology data; Python 3.10+
---

# Batfish Validation (Expert)

Use a reference snapshot and a candidate snapshot to prove intended behavior
and detect unintended reachability. Batfish results are only as trustworthy as
the parsed configurations, topology, vendor support, and supplemental data.

## Core Engineering Capabilities

- Upload snapshots and query BGP sessions, routes, forwarding, ACLs, defined
  structures, reachability, loops, and differential behavior.
- Assert zero undefined/unused references, compatible BGP sessions, expected
  reachability, no forwarding loops, and approved policy deltas.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Validate snapshot parsing and device/vendor coverage before interpreting a
  query result; fail on parse warnings that affect the claim.
- Compare candidate to a known-good reference and encode expected changes as
  assertions. Do not accept “no answer” as proof of safety.
- Keep configs sanitized and supplemental topology/ISP/BGP data versioned with
  the snapshot.
- Scope reachability by source, destination, protocol, ports, VRF, and ingress
  interface; broad queries can hide policy mistakes.
- Record Batfish version, snapshot IDs, query parameters, and evidence with the
  change review.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Collect the vendor configs, topology links, interface addresses, snapshots, and intended reachability or policy assertions. Normalize filenames and topology assumptions before asking Batfish to answer a question.

### Phase 2 (Generation)

Build a reproducible snapshot and a focused Batfish question set for reachability, ACL acceptance, BGP session health, loops, and undefined references. Keep expected failures explicit rather than treating an empty answer as success.

### Phase 3 (Self-Verification)

Run the questions against a known-good and intentionally broken snapshot. Archive the answer tables, identify parser warnings, and distinguish a proven property from a property Batfish could not model.

1. Build reference and candidate snapshots from reviewed artifacts.
2. Validate parsing/topology, run structural and protocol queries.
3. Run differential reachability and loop checks.
4. Fail the change on unexpected results and publish query evidence.

## Production Code / Template Example

### Input / Requirement

Provide sanitized device configurations, topology metadata, snapshot name, required protocols, and the reachability or compliance assertions to prove.

### Output / Generated Code

Return the snapshot layout, Batfish questions, expected answer criteria, and a CI-friendly report that links each failure to a device or topology input.


```python
from pybatfish.client.session import Session
bf = Session(host="localhost")
bf.init_snapshot("candidate", network_name="net")
assert len(bf.q.bgpSessionCompatibility().answer().frame()) == 0
```

Use the actual pybatfish query API for the installed version and assert the
precise expected frame columns/results for the topology.

## Validation, Linting & Testing Commands

- Test malformed config, unsupported syntax, missing supplemental data,
  undefined references, BGP incompatibility, ACL deny/permit, and differential
  reachability cases.
- Review traces for every critical assertion and retain snapshot metadata.
- Run `python3 scripts/validate_skills.py`.

## References

- [pybatfish documentation](https://batfish.readthedocs.io/en/latest/)
- [pybatfish GitHub](https://github.com/batfish/pybatfish)

## Offline Execution Contract

Use local Batfish snapshots and supplied configs whenever possible. Without Batfish or complete vendor parsing support, validate snapshot structure and query intent but do not claim reachability, BGP, ACL, or loop proofs.

## Architecture & Technical Design Patterns

Build a reference snapshot and a candidate snapshot with identical device names,
vendor/version metadata, topology, and supplemental data. Before policy
queries, assert that all configs parse and that the topology contains expected
interfaces/links. Useful proof categories are:

```python
bf.q.bgpSessionCompatibility()
bf.q.undefinedReferences()
bf.q.reachable(// parameters="..." //)
bf.q.forwardingDetail()
```

Use the exact query syntax supported by the installed pybatfish version and
assert returned rows, not merely that a query ran. Differential tests should
encode expected changes and reject new reachability, missing routes, changed
next hops, incompatible BGP sessions, undefined references, ACL violations,
and forwarding loops. Store snapshot name, Batfish version, query parameters,
and evidence traces with the review; a parser warning affecting a query is a
failed validation prerequisite, not a harmless warning.
