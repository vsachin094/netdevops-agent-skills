# netdevops-agent-skills

AI agent skills for network automation — transport, parsing, Ansible, Terraform, testing, observability, operations.

55 skills, each with runnable validators, vendor compatibility tables, and cross-refs.

```bash
python3 scripts/validate_skills.py   # all pass
```

---

## Quick Start

```bash
git clone https://github.com/vsachin094/netdevops-agent-skills.git
cd netdevops-agent-skills
python3 scripts/validate_skills.py
```

**Use a skill** — copy its directory into your project's agent skills folder:

```bash
mkdir -p .agents/skills
cp -R skills/netmiko-core .agents/skills/
cp -R skills/gnmi-client .agents/skills/
```

**Reference in your agent prompt:**

```
Use skills/gnmi-client/SKILL.md.
Build a Python gNMI client that subscribes to interface counters on SR Linux.
Validate with the skill's test suite.
```

---

## Skill Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         netdevops-agent-skills (55)                         │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────────┤
│  TRANSPORT   │  PARSING     │  ANSIBLE     │  TERRAFORM   │  TESTING       │
├──────────────┼──────────────┼──────────────┼──────────────┼────────────────┤
│ netmiko-core │ ntc-textfsm  │ role-creation│ tf-vpc-found │ containerlab   │
│ ncclient-    │ ttp-parsers  │ plugin-dev   │ tf-aws-net   │ batfish-val    │
│   restconf   │ cli-regex    │ ee-build     │ tf-azure-gcp │ network-test   │
│ paramiko-ssh │ pyang-xpath  │ vault-hygiene│ tf-firewall  │ config-diff    │
│ async-net-   │ yang-model   │ dyn-inventory│ tf-state-surg│ config-sanitiz │
│   automation │              │ resource-mod │ tf-module-hrd│ network-change │
│ scrapli-     │              │ linux-net    │ tf-aci-sdwan │ network-config │
│   threaded   │              │ netcli-play  │ tf-to-ansible│   drift-det    │
│ gnmi-client  │              │ pre-post-chk │              │                │
│ gnmi-snmp-   │              │              │              │                │
│   telemetry  │              │              │              │                │
├──────────────┼──────────────┼──────────────┼──────────────┼────────────────┤
│  OBSERVABILITY          │  OPERATIONS            │  UTILITIES               │
├─────────────────────────┼────────────────────────┼──────────────────────────┤
│ network-observability   │ gitops-net-auto        │ ipam-subnetting          │
│                         │ network-device-onboard │ jinja2-network-templates │
│                         │ network-change-runbooks│ cli-tool-packaging       │
│                         │                        │ network-data-pipelines     │
│                         │                        │ network-rest-clients       │
│                         │                        │ network-protocols-as-code  │
│                         │                        │ netbox-nautobot-api        │
│                         │                        │ nornir-napalm              │
│                         │                        │ netconf-automation         │
│                         │                        │ netconf-restconf-payloads  │
│                         │                        │ pysnmp-automation          │
│                         │                        │ pyats-genie                │
│                         │                        │ tf-state-surgery           │
│                         │                        │ ttp-parsers                │
└─────────────────────────┴────────────────────────┴──────────────────────────┘
```

---

## Skills by Category

### Transport (8)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `netmiko-core` | Inventory-driven SSH with Netmiko | Per-device results, config_mode per platform, `--check`/ `--diff`, prompt derivation |
| `ncclient-restconf` | NETCONF/RESTCONF with transactions | Candidate datastore, locks, confirmed commit, TLS, typed payloads |
| `paramiko-ssh` | Raw SSH/SFTP transport | Strict host-key verify, timeouts, command allow-list, jump hosts |
| `async-network-automation` | High-concurrency async SSH/HTTP | Semaphores, bounded queues, cancellation, per-device results |
| `scrapli-netmiko-threaded` | Threaded fleet execution | ThreadPoolExecutor, exception isolation, JSON/CSV output |
| `gnmi-client` | Programmatic gNMI Get/Set/Subscribe | Python + Go, TLS/mTLS, typed values, path helpers |
| `gnmi-snmp-telemetry` | gNMI/SNMP collection config | gnmic, snmp_exporter, PromQL alerts, Grafana dashboards |
| `netconf-automation` | NETCONF automation patterns | Capabilities, filters, edit-config, validated commits |

### Parsing & Modeling (6)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `ntc-textfsm` | TextFSM templates for CLI output | Version handling, Filldown leak tests, NTC index format |
| `ttp-parsers` | Hierarchical TTP templates | Nested config, matchers (IP/MAC), dynamic paths |
| `cli-regex` | Pure Python regex parsers | Named groups, ANSI strip, typed extraction, fixtures |
| `pyang-xpath` | YANG schema inspection | Tree views, exact XPaths, NETCONF/RESTCONF paths |
| `yang-model-dev` | Author YANG 1.1 modules | Constraints, leafrefs, augmentations, pyang lint |
| `network-protocols-as-code` | Vendor-neutral intent → config | L2/L3/BGP/EVPN, multi-vendor render, unsupported feature handling |

### Ansible (9)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `ansible-role-creation` | Reusable multi-vendor roles | Molecule, argument_specs, platform task split, CI |
| `ansible-plugin-development` | Custom modules/filters/connection | DOCUMENTATION/EXAMPLES/RETURN, check_mode, ansible-test |
| `ansible-ee-build` | Pinned execution environments | requirements.yml/txt, bindep.txt, ansible-builder, scan |
| `ansible-vault-hygiene` | Secret management | vault-id per env, no_log boundaries, trufflehog/gitleaks |
| `ansible-dynamic-inventory` | NetBox/AWS/Azure/Terraform sources | keyed_groups, compose, caching, credential safety |
| `ansible-resource-modules` | Declarative network resources | merged/replaced/overridden/deleted, idempotency |
| `ansible-linux-networking` | Linux host networking | Netplan/NM, FRR, nftables, WireGuard, mgmt lockout prevention |
| `ansible-netcli-playbooks` | Foundational network playbooks | FQCNs, network_cli, backup, check_mode |
| `ansible-pre-post-checks` | Change safety wrapper | Baseline → change → verify → rollback, block/rescue/always |

### Terraform (9)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `tf-vpc-foundations` | Base VPC/VNet modules | CIDR validation, flow logs, remote state |
| `tf-aws-networking` | AWS VPC, TGW, DX, FW | Multi-AZ, route associations, propagation |
| `tf-azure-gcp-networking` | Azure/GCP hub-spoke, peering | VNet peering, Cloud Router/NAT, NCC |
| `tf-firewall-policies` | Palo/Forti/Check Point/Cloudflare | Stable keys, shadow analysis, default-deny |
| `tf-module-hardening` | Secure modules | tflint/Trivy/Checkov, pin providers, preconditions |
| `tf-state-surgery` | Declarative state migration | moved/import/removed blocks, zero-destroy verify |
| `tf-aci-sdwan-meraki` | Controller-based (ACI/SD-WAN/Meraki) | Hierarchy, stable for_each, async readiness |
| `tf-to-ansible-inventory` | TF outputs → Ansible inventory | Structured outputs, readiness checks, sensitive handling |
| `tf-state-surgery` | State migration patterns | moved/import/removed, zero-destroy |

### Testing & Validation (6)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `containerlab-topologies` | Lab topologies as code | Pinned images, startup config validation, CI pipeline |
| `batfish-validation` | Mathematical network analysis | BGP/OSPF/ACL/reachability, differential snapshots |
| `network-testing-framework` | pytest + Containerlab + Batfish | Unit/integration/contract, JUnit XML, markers |
| `config-diff-audit` | Config drift detection | Normalization, volatile stripping, secret redaction |
| `config-sanitizer` | Config/log redaction | Deterministic placeholders, topology preservation |
| `network-config-drift-detection` | Scheduled drift detection | Collect → normalize → diff → alert → remediate |

### Observability (1)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `network-observability-stack` | Prometheus/Grafana/Loki/Tempo | snmp_exporter, gnmic, PromQL alerts, runbook URLs |

### Operations (4)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `gitops-network-automation` | ArgoCD/Flux for network config | Kustomize overlays, pre/post sync hooks, drift alerts |
| `network-device-onboarding` | Day-0: ZTP, creds, host-keys, verify | Idempotent, rollback per stage, inventory registration |
| `network-change-runbooks` | Auditable change execution | Pre-checks, approval gates, post-checks, rollback, evidence |
| `nso-device-onboarding` | NSO-specific onboarding | Authgroups, NED assignment, sync-from, compare-config |

### Utilities (12)
| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `ipam-subnetting` | Hierarchical CIDR allocation | VLSM, overlap detection, NetBox/TF seed data |
| `jinja2-network-templates` | Multi-vendor templates + filters | Capability registry, StrictUndefined, IP/MAC filters |
| `cli-tool-packaging` | Packaged Python CLIs | Typer/Click, Rich, dry-run, JSON output, exit codes |
| `network-data-pipelines` | Pandas/Polars + Pydantic | Normalization, cardinality control, quarantine |
| `network-rest-clients` | Typed REST clients for controllers | Timeouts, retries, pagination, idempotency keys |
| `network-protocols-as-code` | Intent → multi-vendor config | BGP/OSPF/EVPN, unsupported feature findings |
| `netbox-nautobot-api` | NetBox/Nautobot client | GraphQL bulk, pagination, dry-run, rate limits |
| `nornir-napalm` | Fleet automation with Nornir | Inventory layers, compare/commit/discard, per-host results |
| `netconf-automation` | NETCONF patterns | Lock/validate/commit, capability check |
| `netconf-restconf-payloads` | XML/JSON payload construction | Schema validation, Pydantic models |
| `pysnmp-automation` | SNMP v1/v2c/v3 async | GET/BULK/SET, traps, MIB resolution |
| `pyats-genie` | Cisco Genie parsers + AEtest | MetaParser, differential pre/post, testbed YAML |
| `pysnmp-automation` | SNMP automation | Async GET/BULK/SET, MIB compilation |
| `ttp-parsers` | Hierarchical text parsing | TTP templates, nested output, matchers |
| `tf-state-surgery` | State migration | moved/import/removed, zero-destroy verify |

---

## Each Skill Contains

```
skills/<skill-slug>/
├── SKILL.md              # Full spec: workflow, guardrails, code, validation
├── scripts/
│   └── validate_*.py     # Runnable validator (pytest, linter, schema check)
└── references/           # (optional) local fixtures, schemas
```

**Run a skill's validator:**
```bash
python3 skills/netmiko-core/scripts/validate_runner.py --help
python3 skills/gnmi-client/scripts/validate_client.py --help
```

---

## Agent Integration

| Agent | Project Location | Explicit Use |
|-------|------------------|--------------|
| Claude Code | `.claude/skills/<slug>/SKILL.md` | `/skill <slug>` |
| GitHub Copilot | `.github/skills` or `.agents/skills` | `/skill <slug>` or natural language |
| Cursor | Workspace + `@skills/<slug>/SKILL.md` | `@skills/<slug>/SKILL.md` |
| Continue | Workspace + `.continue/rules` | Project rule or attached file |
| Local LLM | Any readable directory | Paste SKILL.md or reference path |

---

## Offline Use

Skills work offline with local dependencies. See [references/open-source-local.md](references/open-source-local.md) for:
- Recommended local layout (venv, vendor YANG, fixtures, snapshots)
- Dependency tiers (stdlib → pinned open-source → platform adapters)
- Offline quality gates (local validators, fixtures, dependency contracts)

---

## Contributing

1. Add skill at `skills/<lowercase-hyphenated-slug>/SKILL.md`
2. Include runnable validator in `scripts/`
3. Follow the skill structure (frontmatter + 9 required sections)
4. No credentials, private keys, customer data, proprietary files
5. Run `python3 scripts/validate_skills.py` before PR

---

## License

MIT. Vendor names and product marks remain property of their respective owners.