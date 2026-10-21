---
name: gnmi-snmp-telemetry
description: "[Tier: Intermediate] Generate gNMI streaming telemetry, gnmic/Telegraf inputs, Prometheus snmp_exporter configuration, PromQL alerts, and Grafana dashboard data. Use this skill when network health and utilization need consistent metrics, labels, counters, and alert semantics."
license: MIT
compatibility: gnmic or Telegraf; OpenConfig gNMI; Prometheus; snmp_exporter; Grafana; device telemetry support
---

# gNMI/SNMP Telemetry (Intermediate)

Design telemetry as an observable contract: metric name, labels, units,
sampling/event semantics, retention, cardinality, and alert threshold must be
intentional.

## Core Engineering Capabilities

- Configure OpenConfig gNMI `SAMPLE` and `ON_CHANGE` subscriptions and
  normalize paths into metrics.
- Generate `snmp_exporter` generator config for 64-bit interface counters,
  PromQL alert rules, recording rules, and Grafana dashboard JSON.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Prefer `ifHCInOctets`/`ifHCOutOctets` and calculate utilization with `rate()`
  over a window; account for interface speed and counter resets.
- Keep labels bounded: never use raw descriptions, user IDs, or unbounded
  route/prefix values as labels.
- Use OpenConfig paths and declare encoding, mode, sample interval, and
  authentication/TLS. Do not assume vendor path support.
- Design alert `for` duration, severity, runbook, and inhibition to avoid
  paging on scrape gaps or one transient sample.
- Keep SNMP communities and certificates externalized.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define SLO signal, metric schema, labels, collection mode, and cardinality.
2. Validate device support and generate collector/config assets.
3. Test scrape/stream loss, resets, labels, alert behavior, and dashboard
   queries with representative data.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```promql
100 * rate(ifHCInOctets[5m]) * 8 / (interface_speed_bits_per_second)
```

## Validation, Linting & Testing Commands

- Run Prometheus rule checks and exporter/gNMI config validation.
- Test counter reset, scrape outage, label explosion, and interface-speed
  change cases.
- Run `python3 scripts/validate_skills.py`.

## References

- [Prometheus SNMP exporter](https://github.com/prometheus/snmp_exporter)
- [OpenConfig telemetry](https://github.com/openconfig/telemetry)
- [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)

## Offline Execution Contract

Generate telemetry configuration, PromQL, and dashboard JSON from local schemas and sample metrics. Without devices/exporters/Prometheus, validate metric names, labels, units, and expressions but do not claim collection or alert firing.

## Architecture & Technical Design Patterns

Define every signal as `metric`, `source path/OID`, `type`, `unit`, `labels`,
`collection mode`, and `expected cadence`. Use gNMI `SAMPLE` for continuously
changing counters and `ON_CHANGE` for state/configuration events; set an
explicit sample interval and encoding. For interface bandwidth, use 64-bit
high-capacity counters, calculate `rate(counter[window])`, multiply octets by
8, divide by interface speed, and clamp/handle resets.

Keep labels bounded to device, site, interface, VRF, and role. Never label by
raw description, arbitrary prefix, username, or route count. Alert rules need
threshold, `for`, severity, runbook, and scrape/stream freshness handling.
Test counter reset, exporter outage, stale stream, interface-speed change,
label cardinality, and absent optional metrics with saved samples.
