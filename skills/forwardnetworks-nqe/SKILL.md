---
name: forwardnetworks-nqe
description: "Query and validate modeled network state with Forward Networks Network Query Engine (NQE), including inventory, configuration, routing, policy, and topology questions. Use this skill when an operator needs repeatable, evidence-backed queries in a Forward Networks environment."
license: MIT
compatibility: Forward Networks platform with NQE enabled; query fields and available data depend on the platform release, licensed features, and collected network snapshots
---

# Forward Networks NQE (Advanced)

Use NQE to turn a specific network question into a repeatable query over Forward Networks' modeled network data. Treat query results as evidence about the selected snapshot and model, not as a guarantee about live traffic or uncollected state.

## Core Engineering Capabilities

- Build focused queries for devices, interfaces, addresses, routing, security policy, and topology using the entities and fields available in the target environment.
- Filter and project results so each row answers a clear operational or compliance question.
- Compare query results across devices, sites, VRFs, snapshots, or other supported scopes.
- Use NQE results to identify missing, inconsistent, or unexpected modeled state and direct follow-up investigation.
- Export or operationalize validated results through the platform's supported UI, API, or workflow for the installed release.

## Architecture & Technical Design Patterns

- **Question → model → query → evidence:** State the claim first, identify the modeled entities and fields that can prove it, query those fields, then preserve the result and snapshot context.
- **Narrow before expanding:** Scope by device, site, VRF, protocol, or snapshot before projecting larger nested collections.
- **Prefer structured output:** Return named fields with stable, useful values; avoid opaque concatenated strings when the result will be compared, filtered, or consumed downstream.
- **Separate discovery from assertion:** Explore the model to learn available values, then turn the verified query into a stable check with explicit expected results.
- **Keep checks explainable:** A result should include enough device, interface, route, policy, or snapshot identity to let an operator trace a finding to its source.
- **Make comparisons intentional:** Compare like-for-like snapshots and scopes; account for expected changes instead of treating every difference as a defect.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Confirm NQE syntax, entity names, field paths, enum values, and query features in the target platform's NQE editor, schema browser, and release-matched documentation. Model coverage and names can vary by release and collected data.
- Do not invent fields or infer that an absent result proves a property. An empty result can mean the condition is absent, the scope is wrong, data is missing, or the model cannot represent the question.
- Record the selected network, snapshot or collection time, query text, filters, and relevant model/data limitations with operational findings.
- Validate data freshness and collection status before making claims about current network behavior.
- Distinguish modeled configuration and control-plane state from packet-level forwarding or real-time telemetry. Use the appropriate Forward Networks capability or another measurement source when the question requires evidence beyond NQE's modeled data.
- Scope sensitive data access to the minimum required permissions. Do not put credentials, tokens, customer configurations, or sensitive result data in query text, source control, or unapproved logs.
- Treat query results as read-only evidence unless a separately reviewed workflow explicitly performs a change. Never imply that a query has changed or repaired the network.
- Bound broad queries. Avoid returning entire configurations or unbounded device/interface/route collections when a smaller projection answers the question.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

1. Restate the operational question as a testable claim, including the expected result and the consequence of a violation.
2. Identify the target network, snapshot or time range, devices, sites, VRFs, protocols, and any required exclusions.
3. Confirm NQE is enabled and determine the platform release, query context, available data, and permissions.
4. Identify the model entities and fields needed to answer the question. If any are uncertain, inspect the schema or use the editor's supported discovery and autocomplete before writing a final query.

### Phase 2 (Implementation)

1. Start with the smallest query that returns the required entity identifiers and fields.
2. Add filters that reflect the agreed scope; avoid broad scans and implicit assumptions about missing values.
3. Add derived fields or nested results only when they improve the answer and use supported NQE constructs.
4. Run the query in the target NQE environment and correct syntax, type, and field-path errors using the platform's diagnostics.
5. Convert the verified query into a reusable check or downstream integration only using mechanisms documented for the installed release.

### Phase 3 (Verification)

1. Test representative devices and boundary cases, including devices with missing or unsupported data.
2. Check that known-positive and known-negative examples appear as expected; inspect the underlying device or snapshot when results are surprising.
3. Confirm that query scope, snapshot freshness, permissions, and model coverage support the claim.
4. Save the query, result context, expected output, and limitations with the change, audit, or runbook.
5. Report findings with evidence and uncertainty. Do not convert an unverified or empty result into a pass.

## Production Code / Template Example

### Input / Requirement

Find the devices in a selected Forward Networks network and return a compact inventory with a hostname and vendor. Before using the template, confirm that `network.devices`, `device.name`, and `device.platform.vendor` are present in the target release's NQE schema and that the query editor accepts the shown syntax.

### Output / Generated Code

This starter query uses common NQE query structure, but field paths can differ by tenant and release:

```javascript
foreach device in network.devices
select {
  hostname: device.name,
  vendor: device.platform.vendor
}
```

After confirming those paths in the target schema, expect a result table with `hostname` and `vendor` columns, for example:

| hostname | vendor |
|---|---|
| edge-01 | Cisco |
| spine-01 | Arista |

These rows are illustrative, not platform output. Run the sample in the target NQE editor and compare representative rows with the selected snapshot. If the schema differs, use the editor's supported field discovery and adjust the paths rather than guessing.

### More Sample Queries

The following examples demonstrate common NetOps questions. They use assumed collection names and field paths; confirm each path, status representation, and query construct in the target NQE schema before running. Do not interpret an empty result as proof until collection coverage and query scope are verified.

#### Interface status inventory

Returns modeled admin and operational states for each interface. Confirm the collection and field paths: `network.interfaces`, `interface.device.name`, `interface.name`, `interface.adminStatus`, and `interface.operStatus`.

```javascript
foreach interface in network.interfaces
select {
  device: interface.device.name,
  interface: interface.name,
  adminStatus: interface.adminStatus,
  operStatus: interface.operStatus
}
```

#### BGP neighbor status inventory

Returns the modeled state of each BGP neighbor. Confirm the collection and field paths: `network.bgpNeighbors`, `neighbor.device.name`, `neighbor.remoteAddress`, and `neighbor.state`.

```javascript
foreach neighbor in network.bgpNeighbors
select {
  device: neighbor.device.name,
  remoteAddress: neighbor.remoteAddress,
  state: neighbor.state
}
```

The interface and BGP examples return status inventories rather than deciding what is healthy: operational values and policy expectations vary by network. Add filters or assertions only after confirming the platform's query syntax and the values expected in the scoped environment. For a compliance check, report the device identifier, observed value, expected value, and snapshot context for every violation.

## Validation, Linting & Testing Commands

- In the Forward Networks NQE editor, compile and run each query against the intended network and snapshot.
- Use the editor's schema discovery, autocomplete, and diagnostics to verify identifiers, field paths, types, and supported query constructs.
- Test the query against known-good and known-bad examples and against incomplete or unsupported device data.
- For scheduled or integrated use, validate permissions, documented API/workflow behavior, timeouts, result limits, and failure handling for the installed release.
- Run the repository skill contract check from the repository root:

```bash
python3 scripts/validate_skills.py
```

## References

- Forward Networks official product documentation and in-product NQE editor/schema browser. Use documentation matching the deployed platform release.
- Forward Networks network model and collection-status views for interpreting coverage, freshness, and unsupported data.

## Offline Execution Contract

NQE runs against a Forward Networks environment and its collected network model; this skill cannot execute a query offline. Without access to the target platform, produce a clearly labeled query template and a verification checklist only. Do not claim that the query compiles, that the target fields exist, or that the network passes a check until it has been run and its snapshot context has been verified.

## Related Skills

- [batfish-validation](../batfish-validation/SKILL.md) — Offline analysis of supplied device configurations and topology
- [network-testing-framework](../network-testing-framework/SKILL.md) — Repeatable network tests and validation workflows
- [network-change-runbooks](../network-change-runbooks/SKILL.md) — Attach query evidence to an auditable change process
- [network-observability-stack](../network-observability-stack/SKILL.md) — Live telemetry, metrics, logs, and alerting
