---
name: gnmi-snmp-telemetry
description: "Generate gNMI streaming telemetry, gnmic/Telegraf inputs, Prometheus snmp_exporter configuration, PromQL alerts, and Grafana dashboard data. Use this skill when network health and utilization need consistent metrics, labels, counters, and alert semantics."
license: MIT
compatibility: gnmic or Telegraf; OpenConfig gNMI; Prometheus; snmp_exporter; Grafana; device telemetry support
---

# gNMI/SNMP Telemetry (Intermediate)

Design telemetry as an observable contract: metric name, labels, units, sampling/event semantics, retention, cardinality, and alert threshold must be intentional.

## Core Engineering Capabilities

- Configure OpenConfig gNMI `SAMPLE` and `ON_CHANGE` subscriptions and normalize paths into metrics.
- Generate `snmp_exporter` generator config for 64-bit interface counters, PromQL alert rules, recording rules, and Grafana dashboard JSON.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Prefer `ifHCInOctets`/`ifHCOutOctets` and calculate utilization with `rate()` over a window; account for interface speed and counter resets.
- Keep labels bounded: never use raw descriptions, user IDs, or unbounded route/prefix values as labels.
- Use OpenConfig paths and declare encoding, mode, sample interval, and authentication/TLS. Do not assume vendor path support.
- Design alert `for` duration, severity, runbook, and inhibition to avoid paging on scrape gaps or one transient sample.
- Keep SNMP communities and certificates externalized.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Define the source models, gNMI paths or SNMP OIDs, encoding, scrape interval, labels, retention, alert thresholds, and cardinality budget. Check that the requested paths exist in the target release or local schema.

### Phase 2 (Implementation)

Generate collector configuration, normalized metric names, PromQL rules, and dashboard panels with explicit labels and ownership. Keep secrets external and avoid labels derived from unbounded device data.

### Phase 3 (Verification)

Validate configuration syntax, replay local telemetry fixtures, evaluate alert expressions for firing and recovery, and inspect series cardinality. Mark live subscription and device support as unverified without a target.

1. Define SLO signal, metric schema, labels, collection mode, and cardinality.
2. Validate device support and generate collector/config assets.
3. Test scrape/stream loss, resets, labels, alert behavior, and dashboard queries with representative data.

## Production Code / Template Example

### Input / Requirement

Provide telemetry paths or OIDs, target versions, collector endpoints, label policy, retention requirements, and alert acceptance criteria.

### Output / Generated Code

Return collector configuration, sample metrics, PromQL alerts, dashboard JSON where requested, and tests for missing, stale, and recovered telemetry.

```promql
# Interface utilization (64-bit counters)
100 * rate(ifHCInOctets[5m]) * 8 / (interface_speed_bits_per_second)

# BGP peer state
bgp_peer_state{state="established"} == 1

# Alert: interface utilization > 80% for 5m
- alert: InterfaceHighUtilization
  expr: |
    (100 * rate(ifHCInOctets[5m]) * 8 / interface_speed_bits_per_second) > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Interface {{ $labels.interface }} on {{ $labels.device }} > 80% utilization"
    runbook_url: "https://runbooks.netops.io/interface-utilization"
```

```yaml
# snmp_exporter generator.yml
modules:
  if_mib:
    walk:
      - 1.3.6.1.2.1.2.2.1.1   # ifIndex
      - 1.3.6.1.2.1.2.2.1.2   # ifDescr
      - 1.3.6.1.2.1.2.2.1.5   # ifSpeed
      - 1.3.6.1.2.1.31.1.1.1.6  # ifHCInOctets
      - 1.3.6.1.2.1.31.1.1.1.10 # ifHCOutOctets
    metric_prefix: interface_
    version: 2
    auth:
      community: ${{SNMP_COMMUNITY}}
```

```yaml
# gnmic config.yml
inputs:
  gnmi:
    address: "192.0.2.10:57400"
    subscription:
      - path: /interfaces/interface/state/counters
        mode: SAMPLE
        sample_interval: 10s
        encoding: PROTO
    authentication:
      username: "${GNMI_USER}"
      password: "${GNMI_PASS}"
```

## Validation, Linting & Testing Commands

- Run Prometheus rule checks and exporter/gNMI config validation.
- Test counter reset, scrape outage, label explosion, and interface-speed change cases.
- Run `python3 scripts/validate_skills.py`.

## References

- [Prometheus SNMP exporter](https://github.com/prometheus/snmp_exporter)
- [OpenConfig telemetry](https://github.com/openconfig/telemetry)
- [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)

## Offline Execution Contract

Generate telemetry configuration, PromQL, and dashboard JSON from local schemas and sample metrics. Without devices/exporters/Prometheus, validate metric names, labels, units, and expressions but do not claim collection or alert firing.

## Architecture & Technical Design Patterns

Define every signal as `metric`, `source path/OID`, `type`, `unit`, `labels`, `collection mode`, and `expected cadence`. Use gNMI `SAMPLE` for continuously changing counters and `ON_CHANGE` for state/configuration events; set an explicit sample interval and encoding. For interface bandwidth, use 64-bit high-capacity counters, calculate `rate(counter[window])`, multiply octets by 8, divide by interface speed, and clamp/handle resets.

Keep labels bounded to device, site, interface, VRF, and role. Never label by raw description, arbitrary prefix, username, or route count. Alert rules need threshold, `for`, severity, runbook, and scrape/stream freshness handling. Test counter reset, exporter outage, stale stream, interface-speed change, label cardinality, and absent optional metrics with saved samples.