---
name: network-change-runbooks
description: "[Tier: Intermediate] Build executable network change runbooks with pre-checks, post-checks, rollback steps, approval gates, and evidence collection. Use this skill when a network change requires an auditable, testable, and reversible execution plan before touching production devices."
license: MIT
compatibility: Python 3.10+; Jinja2; YAML/JSON; Git; optional Ansible, Terraform, or vendor CLI transport; device simulator or lab for validation
---

# Network Change Runbooks (Intermediate)

A runbook is executable, not documentation. It encodes intent, validates preconditions, executes atomically where possible, verifies outcomes, and defines rollback. Every step must be testable without production access.

## Core Engineering Capabilities

- Model change intent as structured data (device scope, config delta, protocol impact, risk tier, owner, approval chain).
- Generate pre-checks: reachability, adjacency state, config diff sanity, capacity headroom, maintenance window alignment.
- Render executable steps with explicit success/failure conditions, timeouts, and rollback triggers.
- Enforce approval gates: human, automated policy, or scheduled window; capture evidence at each gate.
- Produce post-checks: protocol convergence, route tables, interface state, telemetry baselines, config audit.
- Output machine-readable evidence (JSON) for CI, ticketing, and audit trails.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never execute a mutation without a preceding pre-check that passed and an explicit approval record.
- Every destructive step must have a corresponding rollback step with the same or lower risk tier.
- Pre-checks and post-checks must be idempotent and safe to run multiple times.
- Runbooks must fail fast: any pre-check failure blocks execution; any post-check failure triggers rollback evaluation.
- Keep secrets external; never embed credentials, tokens, or keys in the runbook or generated artifacts.
- Validate configuration syntax and semantics (parser, dry-run, digital twin) before any deployment step.
- Use deterministic ordering: group by device, then by dependency (underlay → overlay, infra → service).
- A runbook that cannot be fully validated in a lab/simulator is incomplete; mark unvalidated steps explicitly.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake ### Phase 1 (Ingestion & Validation) Scope)

Collect the change request: device inventory, config delta (or intent model), protocol impact, risk assessment, maintenance window, approval requirements, rollback SLA, and post-check success criteria. Reject requests missing scope, approval path, or rollback definition.

### Phase 2 (Implementation)

Generate a runbook YAML with metadata, pre-checks, execution steps, approval gates, post-checks, and rollback procedures. Render device-specific commands from templates, validate syntax, and produce a dry-run artifact. Keep human-readable markdown and machine-readable JSON in sync.

### Phase 3 (Verification)

Validate the runbook structure, run pre-checks against lab/simulator fixtures, execute dry-run steps, verify post-check logic, and test rollback paths. Confirm evidence schema matches CI/ticketing expectations.

1. Parse change request, validate required fields, and normalize device scope.
2. Generate pre-checks (reachability, adjacency, config diff, capacity, window).
3. Render execution steps from templates; validate each command with parser/dry-run.
4. Define approval gates with conditions, owners, and evidence requirements.
5. Generate post-checks (convergence, routes, interfaces, telemetry, audit).
6. Define rollback steps with triggers, commands, and verification.
7. Output runbook YAML, markdown summary, JSON evidence schema, and test fixtures.

## Production Code / Template Example

### Input / Requirement

Provide the change scope: target devices, configuration delta or intent model, protocol impact (BGP/OSPF/EVPN), risk tier, maintenance window, approval chain, rollback SLA, and success criteria for pre/post checks.

### Output / Generated Code

Return the runbook YAML, rendered markdown, device command files, pre/post-check scripts, rollback procedures, evidence schema, and validation results from lab/simulator.

```yaml
# runbook.yaml
metadata:
  id: cr-2026-0042
  title: "Add VLAN 200 to leaf pair leaf-01/02"
  risk_tier: 2
  maintenance_window: "2026-10-25T02:00:00Z/PT2H"
  owner: "neteng-core"
  approvers: ["neteng-lead", "sre-oncall"]
  rollback_sla: "PT15M"
  change_type: "config_add"

pre_checks:
  - name: "reachability"
    type: "icmp"
    targets: ["leaf-01", "leaf-02"]
    timeout: 5
  - name: "bgp_adjacency"
    type: "cli"
    command: "show ip bgp summary | include Estab"
    targets: ["leaf-01", "leaf-02"]
    expect_count: 4
  - name: "config_diff_sanity"
    type: "diff"
    baseline: "running"
    candidate: "rendered"
    max_changes: 50

execution:
  - step: 1
    device: "leaf-01"
    action: "configure"
    commands_file: "leaf-01-vlan200.cfg"
    validate_before: true
    timeout: 60
    rollback_on_fail: true
  - step: 2
    device: "leaf-02"
    action: "configure"
    commands_file: "leaf-02-vlan200.cfg"
    validate_before: true
    timeout: 60
    rollback_on_fail: true

approval_gates:
  - gate: "pre_check_passed"
    type: "automated"
    condition: "all_pre_checks_passed"
  - gate: "human_approval"
    type: "manual"
    approvers: ["neteng-lead"]
    evidence_required: ["pre_check_report", "config_diff"]
  - gate: "window_open"
    type: "scheduled"
    window: "2026-10-25T02:00:00Z/PT2H"

post_checks:
  - name: "vlan_operational"
    type: "cli"
    command: "show vlan id 200"
    targets: ["leaf-01", "leaf-02"]
    expect: "active"
  - name: "bgp_converged"
    type: "cli"
    command: "show ip bgp summary | include Estab"
    targets: ["leaf-01", "leaf-02"]
    expect_count: 4
    retry: 3
    interval: 10
  - name: "telemetry_baseline"
    type: "promql"
    query: "rate(interface_errors_total[5m]) < 0.01"
    targets: ["leaf-01", "leaf-02"]

rollback:
  trigger: "post_check_failed | manual_abort"
  steps:
    - device: "leaf-01"
      action: "configure"
      commands_file: "leaf-01-vlan200-rollback.cfg"
      validate_before: true
    - device: "leaf-02"
      action: "configure"
      commands_file: "leaf-02-vlan200-rollback.cfg"
      validate_before: true
  verification:
    - name: "vlan_removed"
      type: "cli"
      command: "show vlan id 200"
      targets: ["leaf-01", "leaf-02"]
      expect: "not_present"
```

## Validation, Linting & Testing Commands

- Validate runbook schema: `python -m jsonschema -i runbook.yaml schema/runbook.schema.json`
- Lint device command files: vendor-specific syntax check (e.g., `ansible-playbook --syntax-check`, `containerlab deploy -t topology.clab.yml && ansible-playbook -i inventory.yml validate.yml`)
- Test pre-checks against lab fixtures: `pytest tests/test_prechecks.py -v`
- Test post-checks against lab fixtures: `pytest tests/test_postchecks.py -v`
- Test rollback path: apply runbook in lab, force post-check failure, verify rollback executes and verification passes
- Evidence schema validation: `python -m jsonschema -i evidence.json schema/evidence.schema.json`
- Run `python3 scripts/validate_skills.py` from repository root.

## References

- [Network Change Management Best Practices](https://www.ietf.org/rfc/rfc3934.txt)
- [Ansible Network Modules](https://docs.ansible.com/ansible/latest/collections/cisco/ios/index.html)
- [Containerlab for Network Testing](https://containerlab.dev/)
- [GitOps for Networking](https://www.gitops.tech/)

## Offline Execution Contract

Generate runbook YAML, markdown, command files, and evidence schema from local templates and fixtures. Validate structure, syntax, and logic against recorded device outputs. Without lab/simulator access, mark execution steps and post-checks as unvalidated; do not claim production readiness.

## Architecture & Technical Design Patterns

Runbook structure separates immutable metadata from executable phases:

```yaml
metadata: {id, title, risk_tier, window, owner, approvers, rollback_sla, change_type}
pre_checks: [{name, type, targets, command, expect, timeout}]
execution: [{step, device, action, commands_file, validate_before, timeout, rollback_on_fail}]
approval_gates: [{gate, type, condition, approvers, evidence_required}]
post_checks: [{name, type, targets, command, expect, retry, interval}]
rollback: {trigger, steps: [...], verification: [...]}
```

Pre-check types: `icmp`, `cli`, `snmp`, `gnmi`, `restconf`, `diff`, `capacity`, `window`.
Execution actions: `configure`, `replace`, `commit`, `checkpoint`, `script`.
Post-check types: `cli`, `snmp`, `gnmi`, `promql`, `restconf`, `diff`, `audit`.
Rollback triggers: `post_check_failed`, `manual_abort`, `timeout`, `pre_check_regression`.

Command files use Jinja2 templates with device facts; render per device, validate with platform parser (e.g., `pyang --lint`, vendor syntax check, Batfish), then write to `commands/`. Evidence emitted at each gate: `{gate, timestamp, status, artifacts: [...], operator: ...}`. Exit codes: `0` success, `1` validation error, `2` pre-check failed, `3` approval denied, `4` execution failed, `5` post-check failed, `6` rollback failed.

## Transport Version Compatibility

| Transport | Library | Version | check_mode | diff_mode | rollback |
|-----------|---------|---------|------------|-----------|----------|
| NETCONF | ncclient | 0.6.15+ | ✓ | ✓ | ✓ (candidate) |
| RESTCONF | httpx | 0.25+ | ✓ | ✓ | ✓ (candidate) |
| CLI/SSH | Netmiko | 4.3+ | ✓ | ✓ | Manual |
| CLI/SSH | Scrapli | 2023.12+ | ✓ | ✓ | Manual |
| gNMI | gnmic | 0.20+ | ✗ | ✗ | Manual |
| Ansible | network_cli | 2.15+ | ✓ | ✓ | ✓ (backup) |

**Notes:**
- NETCONF candidate datastore required for native rollback
- RESTCONF `candidate` datastore optional (vendor-dependent)
- CLI rollback requires explicit rollback commands file
- Ansible `ios_config` backup: true provides automatic rollback
- gNMI SetRequest has no native rollback; use config replace

## Related Skills

- [netmiko-core](netmiko-core.md) — CLI transport for runbook execution
- [ncclient-restconf](ncclient-restconf.md) — NETCONF/RESTCONF transport with transaction support
- [ansible-pre-post-checks](ansible-pre-post-checks.md) — Ansible-native pre/post check pattern
- [containerlab-topologies](containerlab-topologies.md) — Lab validation for runbook execution
- [batfish-validation](batfish-validation.md) — Mathematical pre/post verification
- [ansible-vault-hygiene](ansible-vault-hygiene.md) — Secret management in runbooks
- [nac-cicd-pipelines](nac-cicd-pipelines.md) — CI/CD pipeline integration for runbook gates