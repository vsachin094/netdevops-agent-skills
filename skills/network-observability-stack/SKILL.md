---
name: network-observability-stack
description: "Deploy a production-grade network observability stack with Prometheus, Grafana, Alertmanager, Loki, and Tempo for metrics, logs, traces, and flow data. Use this skill when network telemetry must be collected, correlated, and alerted on with consistent labels, cardinality control, and runbook integration."
license: MIT
compatibility: Kubernetes 1.27+ or Docker Compose; Prometheus 2.45+; Grafana 10+; Loki 2.9+; Tempo 2.3+; Alertmanager 0.26+; snmp_exporter; gnmic; Telegraf
---

# Network Observability Stack (Advanced)

Treat observability as a platform, not a collection of tools. Standardize labels, control cardinality, define SLOs, and integrate alerts with runbooks.

## Core Engineering Capabilities

- Deploy Prometheus with service discovery for network devices (static, Consul, Kubernetes, file_sd).
- Configure snmp_exporter generator for 64-bit interface counters, BGP, OSPF, and vendor-specific MIBs.
- Set up gnmic for gNMI streaming telemetry (OpenConfig, vendor paths) with Prometheus remote write.
- Deploy Loki for syslog/config log aggregation with structured labels (device, site, severity, facility).
- Deploy Tempo for distributed tracing of API calls (NETCONF, RESTCONF, gNMI) with W3C tracecontext.
- Build Grafana dashboards with templated variables (site, device, interface) and provisioned datasources.
- Define PromQL alert rules with `for` duration, severity, runbook URLs, and inhibition rules.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Control label cardinality: never use raw descriptions, user IDs, or unbounded route prefixes as labels.
- Use 64-bit counters (`ifHCInOctets`/`ifHCOutOctets`) and calculate utilization with `rate()` over 5m window.
- Account for interface speed and counter resets; clamp utilization at 100%.
- Design alert `for` duration (5m+) to avoid paging on scrape gaps or transient samples.
- Include runbook URLs and inhibition rules in every alert; group related alerts.
- Keep SNMP communities, gNMI tokens, and TLS certs in secrets; never in config maps.
- Use recording rules for expensive queries (e.g., `instance:interface_utilization:ratio`).
- Retention: metrics 14d (hot), 1y (cold); logs 30d; traces 7d (sampled 10%).

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Define the device fleet, telemetry sources (SNMP, gNMI, syslog, NetFlow), label taxonomy, SLOs, alert thresholds, and integration points (ticketing, paging, runbooks).

### Phase 2 (Implementation)

1. **Prometheus** — `prometheus.yml` with file_sd for device targets, relabeling for consistent labels.
2. **snmp_exporter** — `generator.yml` with modules for if_mib, bgp, ospf, vendor MIBs.
3. **gnmic** — Config with subscriptions, outputs (Prometheus remote write), and TLS auth.
4. **Loki** — Promtail pipeline for syslog parsing, structured labels, multiline handling.
5. **Tempo** — OpenTelemetry collector for trace ingestion, sampling policies.
6. **Grafana** — Provisioned datasources, dashboards as code (JSON), templated variables.
7. **Alertmanager** — Routes, inhibition, receivers (PagerDuty, Slack, email), templates.

### Phase 3 (Verification)

Validate: scrape targets UP, metric cardinality within budget, alerts fire/recover correctly, dashboards render, logs searchable, traces correlated. Run chaos test: disconnect device → verify alert → reconnect → verify recovery.

1. `promtool check rules rules/*.yml`
2. `snmp_exporter --config.file=generator.yml` — validate generator
3. `gnmic --config config.yml subscribe` — test subscription
4. Load test: `hey -n 10000 -c 50 http://prometheus/-/ready`
5. Alert test: `amtool alert add alertname=InterfaceDown severity=critical`

## Production Code / Template Example

### Input / Requirement

Provide device inventory, telemetry capabilities, label schema, SLO definitions, alert thresholds, and runbook mappings.

### Output / Generated Code

Return Prometheus config, snmp_exporter generator, gnmic config, Loki/Promtail config, Grafana dashboards, Alertmanager config, and validation scripts.

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 30s
  evaluation_interval: 30s
  external_labels:
    cluster: network-prod
    team: netops

scrape_configs:
  - job_name: network-devices
    file_sd_configs:
      - files:
          - targets/*.yml
        refresh_interval: 1m
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
      - source_labels: [site]
        target_label: site
      - source_labels: [role]
        target_label: role
      - source_labels: [platform]
        target_label: platform
    metrics_path: /metrics
    scheme: http

  - job_name: snmp
    static_configs:
      - targets:
          - snmp-exporter:9116
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: snmp-exporter:9116

  - job_name: gnmi
    static_configs:
      - targets:
          - gnmic:9820
```

```yaml
# snmp_exporter/generator.yml
modules:
  if_mib:
    walk:
      - 1.3.6.1.2.1.2.2.1.1   # ifIndex
      - 1.3.6.1.2.1.2.2.1.2   # ifDescr
      - 1.3.6.1.2.1.2.2.1.5   # ifSpeed
      - 1.3.6.1.2.1.31.1.1.1.6   # ifHCInOctets
      - 1.3.6.1.2.1.31.1.1.1.10  # ifHCOutOctets
      - 1.3.6.1.2.1.2.2.1.7   # ifAdminStatus
      - 1.3.6.1.2.1.2.2.1.8   # ifOperStatus
    metric_prefix: interface_
    version: 2
    auth:
      community: ${{SNMP_COMMUNITY}}

  bgp4_mib:
    walk:
      - 1.3.6.1.2.1.15.3.1.2   # bgpPeerRemoteAs
      - 1.3.6.1.2.1.15.3.1.3   # bgpPeerState
      - 1.3.6.1.2.1.15.3.1.9   # bgpPeerInUpdates
      - 1.3.6.1.2.1.15.3.1.10  # bgpPeerOutUpdates
    metric_prefix: bgp_
    version: 2
```

```yaml
# gnmic/config.yml
inputs:
  gnmi:
    address: "192.0.2.10:57400"
    subscription:
      - path: /interfaces/interface/state/counters
        mode: SAMPLE
        sample_interval: 10s
        encoding: PROTO
      - path: /network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state
        mode: ON_CHANGE
        encoding: PROTO
    authentication:
      username: "${GNMI_USER}"
      password: "${GNMI_PASS}"
    tls:
      ca_file: "/etc/gnmic/ca.pem"
      cert_file: "/etc/gnmic/cert.pem"
      key_file: "/etc/gnmic/key.pem"

outputs:
  prometheus:
    address: "prometheus:9090/api/v1/write"
    external_labels:
      source: gnmi
```

```promql
# rules/network-alerts.yml
groups:
  - name: network-interfaces
    rules:
      - alert: InterfaceHighUtilization
        expr: |
          (100 * rate(ifHCInOctets[5m]) * 8 / interface_ifSpeed) > 80
        for: 5m
        labels:
          severity: warning
          team: netops
        annotations:
          summary: "Interface {{ $labels.ifDescr }} on {{ $labels.instance }} > 80% utilization"
          runbook_url: "https://runbooks.netops.io/interface-utilization"

      - alert: InterfaceDown
        expr: interface_ifOperStatus != 1
        for: 2m
        labels:
          severity: critical
          team: netops
        annotations:
          summary: "Interface {{ $labels.ifDescr }} on {{ $labels.instance }} is down"
          runbook_url: "https://runbooks.netops.io/interface-down"

      - alert: BGPPeerDown
        expr: bgp_bgpPeerState != 6
        for: 3m
        labels:
          severity: critical
          team: netops
        annotations:
          summary: "BGP peer {{ $labels.bgpPeerRemoteAddr }} on {{ $labels.instance }} is down"
          runbook_url: "https://runbooks.netops.io/bgp-peer-down"

  - name: network-capacity
    rules:
      - alert: HighInterfaceErrorRate
        expr: |
          rate(interface_ifInErrors[5m]) + rate(interface_ifOutErrors[5m]) > 0.01
        for: 10m
        labels:
          severity: warning
```

```json
# grafana/dashboards/interface-utilization.json
{
  "dashboard": {
    "title": "Interface Utilization",
    "templating": {
      "list": [
        {"name": "site", "type": "query", "datasource": "Prometheus", "query": "label_values(site)"},
        {"name": "device", "type": "query", "datasource": "Prometheus", "query": "label_values(site=\"$site\", instance)"},
        {"name": "interface", "type": "query", "datasource": "Prometheus", "query": "label_values(site=\"$site\", instance=\"$device\", ifDescr)"}
      ]
    },
    "panels": [
      {
        "title": "In/Out Utilization %",
        "type": "timeseries",
        "datasource": "Prometheus",
        "targets": [
          {"expr": "100 * rate(ifHCInOctets{instance=\"$device\",ifDescr=\"$interface\"}[5m]) * 8 / ifSpeed", "legendFormat": "In %"},
          {"expr": "100 * rate(ifHCOutOctets{instance=\"$device\",ifDescr=\"$interface\"}[5m]) * 8 / ifSpeed", "legendFormat": "Out %"}
        ]
      }
    ]
  }
}
```

## Validation, Linting & Testing Commands

- `promtool check rules rules/*.yml` — validate PromQL syntax
- `promtool check config prometheus.yml` — validate Prometheus config
- `snmp_exporter --config.file=generator.yml` — test generator
- `gnmic --config config.yml subscribe --dry-run` — test gNMI subscription
- `grafana cli admin verify-dashboard dashboard.json` — validate dashboard
- Cardinality check: `curl -s prometheus:9090/api/v1/label/__name__/values | jq '.data | length'`
- Run `python3 scripts/validate_skills.py`.

## References

- [Prometheus best practices](https://prometheus.io/docs/practices/naming/)
- [snmp_exporter generator](https://github.com/prometheus/snmp_exporter/tree/main/generator)
- [gnmic documentation](https://gnmic.kmrd.dev/)
- [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)

## Offline Execution Contract

Generate configuration files and validate syntax locally. Without a running stack, verify configs with lint tools; do not claim metric collection, alert firing, or dashboard rendering.

## Architecture & Technical Design Patterns

**Label Taxonomy (Required):**
```
device: hostname (FQDN or short)
site: datacenter/site code
role: spine/leaf/edge/wan/core
platform: iosxe/nxos/eos/junos/frr/srl
vendor: cisco/arista/juniper/nokia/frrouting
```

**Cardinality Control:**
- Drop high-cardinality labels at scrape: `metric_relabel_configs` to drop `ifAlias`, `description`
- Use recording rules for expensive computations
- Limit `metric_name` count via `scrape_config.metric_relabel_configs`

**Alert Design Pattern:**
```yaml
- alert: AlertName
  expr: <promql>  # Returns 0/1 or value
  for: 5m         # Sustained condition
  labels:
    severity: critical|warning|info
    team: netops
    runbook: <url>
  annotations:
    summary: Human-readable with {{ $labels }}
    runbook_url: <url>
```

**Recording Rules for Expensive Queries:**
```yaml
groups:
  - name: recordings
    rules:
      - record: instance:interface_utilization:ratio
        expr: |
          (rate(ifHCInOctets[5m]) * 8 / ifSpeed) + (rate(ifHCOutOctets[5m]) * 8 / ifSpeed)
      - record: instance:bgp_peers_established:count
        expr: count(bgp_bgpPeerState == 6) by (instance)
```

**Runbook Integration:**
- Every alert annotation includes `runbook_url`
- Runbooks stored in Git alongside configs
- Alertmanager templates include runbook link in notifications

**Related Skills:**

- [gnmi-snmp-telemetry](gnmi-snmp-telemetry.md) — Telemetry collection config for this stack
- [network-testing-framework](network-testing-framework.md) — Validate observability in CI
- [network-change-runbooks](network-change-runbooks.md) — Alerts link to runbooks
- [gitops-network-automation](gitops-network-automation.md) — Deploy stack via GitOps
- [cli-tool-packaging](cli-tool-packaging.md) — Package observability CLI tools