# netdevops-agent-skills

AI agent skills for network automation — transport, parsing, Ansible, Terraform, testing, observability, operations, and Cisco NSO.

Each skill is organized in its own directory around a `SKILL.md`. Depending on the topic, a skill may also include examples, scripts, references, compatibility notes, and links to related skills.

```bash
python3 scripts/validate_skills.py
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
Follow the skill's verification steps and run any applicable tests.
```

---

## Skill Map

```mermaid
graph TD
    classDef transport fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef parsing fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef ansible fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef terraform fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef testing fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef observability fill:#f1f8e9,stroke:#558b2f,stroke-width:2px;
    classDef operations fill:#e0f2f1,stroke:#00695c,stroke-width:2px;
    classDef nso fill:#ede7f6,stroke:#5e35b1,stroke-width:2px;
    classDef utilities fill:#fafafa,stroke:#616161,stroke-width:2px;

    subgraph TRANSPORT["Transport (8)"]
        T1[netmiko-core]
        T2[ncclient-restconf]
        T3[paramiko-ssh]
        T4[async-network-automation]
        T5[scrapli-netmiko-threaded]
        T6[gnmi-client]
        T7[gnmi-snmp-telemetry]
        T8[netconf-automation]
    end

    subgraph PARSING["Parsing & Modeling (6)"]
        P1[ntc-textfsm]
        P2[ttp-parsers]
        P3[cli-regex]
        P4[pyang-xpath]
        P5[yang-model-dev]
        P6[network-protocols-as-code]
    end

    subgraph ANSIBLE["Ansible (9)"]
        A1[ansible-role-creation]
        A2[ansible-custom-plugins]
        A3[ansible-ee-build]
        A4[ansible-vault-hygiene]
        A5[ansible-dynamic-inventory]
        A6[ansible-resource-modules]
        A7[ansible-linux-networking]
        A8[ansible-netcli-playbooks]
        A9[ansible-pre-post-checks]
    end

    subgraph TERRAFORM["Terraform (8)"]
        TF1[tf-vpc-foundations]
        TF2[tf-aws-networking]
        TF3[tf-azure-gcp-networking]
        TF4[tf-firewall-policies]
        TF5[tf-module-hardening]
        TF6[tf-state-surgery]
        TF7[tf-aci-sdwan-meraki]
        TF8[tf-to-ansible-inventory]
    end

    subgraph TESTING["Testing & Validation (10)"]
        V1[containerlab-topologies]
        V2[batfish-validation]
        V3[network-testing-framework]
        V4[config-diff-audit]
        V5[config-sanitizer]
        V6[network-config-drift-detection]
        V7[forwardnetworks-nqe]
        V8[terraform-opa-policy]
        V9[gh-actions-network-ci]
        V10[cis-network-compliance]
    end

    subgraph OBSERVABILITY["Observability (1)"]
        O1[network-observability-stack]
    end

    subgraph OPERATIONS["Operations (4)"]
        OP1[gitops-network-automation]
        OP2[network-device-onboarding]
        OP3[network-change-runbooks]
        OP4[asa-config-backup-restore]
    end

    subgraph NSO["Cisco NSO (5)"]
        N1[nso-device-onboarding]
        N2[nso-nano-services]
        N3[nso-python-fastmap]
        N4[nso-service-package-development]
        N5[nso-xml-templates]
    end

    subgraph UTILITIES["Utilities (14)"]
        U1[ipam-subnetting]
        U2[jinja2-network-templates]
        U3[cli-tool-packaging]
        U4[network-data-pipelines]
        U5[network-rest-clients]
        U6[netbox-nautobot-api]
        U7[nornir-napalm]
        U8[netconf-restconf-payloads]
        U9[pysnmp-automation]
        U10[pyats-genie]
        U11[k8s-network-policy]
        U12[vault-network-secrets]
    end

    %% Key cross-category relationships
    T6 -.-> O1
    T7 -.-> O1
    V1 --> V3
    V2 --> V3
    V4 --> V6
    V5 --> V6
    V7 --> V3
    OP1 --> V1
    OP2 --> V1
    OP3 --> V4
    A9 --> OP3
    U2 --> P6
    A1 --> OP3
    TF8 --> A5
    P6 --> A6
    T8 --> A7
    P4 --> P1
    P4 --> P2

    class T1,T2,T3,T4,T5,T6,T7,T8 transport;
    class P1,P2,P3,P4,P5,P6 parsing;
    class A1,A2,A3,A4,A5,A6,A7,A8,A9 ansible;
    class TF1,TF2,TF3,TF4,TF5,TF6,TF7,TF8 terraform;
    class V1,V2,V3,V4,V5,V6,V7,V8,V9,V10 testing;
    class O1 observability;
    class OP1,OP2,OP3,OP4 operations;
    class N1,N2,N3,N4,N5 nso;
    class U1,U2,U3,U4,U5,U6,U7,U8,U9,U10,U11,U12 utilities;
```

---

## Skills by Category

### Transport (8)
| Skill | Purpose |
|-------|---------|
| `netmiko-core` | Inventory-driven SSH with Netmiko — per-device results, config_mode per platform, `--check`/`--diff` |
| `ncclient-restconf` | NETCONF/RESTCONF with transactions — candidate datastore, locks, confirmed commit |
| `paramiko-ssh` | Raw SSH/SFTP — strict host-key verify, timeouts, command allow-list |
| `async-network-automation` | High-concurrency async SSH/HTTP — semaphores, bounded queues, cancellation |
| `scrapli-netmiko-threaded` | Threaded fleet execution — ThreadPoolExecutor, exception isolation |
| `gnmi-client` | Programmatic gNMI Get/Set/Subscribe — Python + Go, TLS/mTLS, typed values |
| `gnmi-snmp-telemetry` | gNMI/SNMP collection config — gnmic, snmp_exporter, PromQL alerts |
| `netconf-automation` | NETCONF patterns — capabilities, filters, edit-config, validated commits |

### Parsing & Modeling (6)
| Skill | Purpose |
|-------|---------|
| `ntc-textfsm` | TextFSM templates — version handling, Filldown leak tests, NTC index |
| `ttp-parsers` | Hierarchical TTP — nested config, matchers, dynamic paths |
| `cli-regex` | Pure Python regex — named groups, ANSI strip, typed extraction |
| `pyang-xpath` | YANG schema inspection — tree views, exact XPaths |
| `yang-model-dev` | Author YANG 1.1 modules — constraints, leafrefs, pyang lint |
| `network-protocols-as-code` | Vendor-neutral intent → config — L2/L3/BGP/EVPN, multi-vendor |

### Ansible (9)
| Skill | Purpose |
|-------|---------|
| `ansible-role-creation` | Reusable multi-vendor roles — Molecule, argument_specs, platform task split |
| `ansible-custom-plugins` | Custom Ansible modules, filters, and connection plugins — check mode, ansible-test |
| `ansible-ee-build` | Pinned execution environments — requirements.yml/txt, bindep.txt |
| `ansible-vault-hygiene` | Secret management — vault-id per env, no_log boundaries, trufflehog/gitleaks |
| `ansible-dynamic-inventory` | NetBox/AWS/Azure/Terraform sources — keyed_groups, compose, caching |
| `ansible-resource-modules` | Declarative network resources — merged/replaced/overridden/deleted |
| `ansible-linux-networking` | Linux host networking — Netplan/NM, FRR, nftables, WireGuard |
| `ansible-netcli-playbooks` | Foundational network playbooks — FQCNs, network_cli, backup |
| `ansible-pre-post-checks` | Change safety wrapper — baseline → change → verify → rollback |

### Terraform (8)
| Skill | Purpose |
|-------|---------|
| `tf-vpc-foundations` | Base VPC/VNet modules — CIDR validation, flow logs |
| `tf-aws-networking` | AWS VPC, TGW, DX, firewall — multi-AZ, route associations |
| `tf-azure-gcp-networking` | Azure/GCP hub-spoke, peering — VNet peering, Cloud Router/NAT |
| `tf-firewall-policies` | Palo/Forti/Check Point/Cloudflare — stable keys, shadow analysis |
| `tf-module-hardening` | Secure modules — tflint/Trivy/Checkov, pin providers |
| `tf-state-surgery` | Declarative state migration — moved/import/removed blocks |
| `tf-aci-sdwan-meraki` | Controller-based — hierarchy, stable for_each, async readiness |
| `tf-to-ansible-inventory` | TF outputs → Ansible inventory — structured outputs, readiness checks |

### Testing & Validation (8)
| Skill | Purpose |
|-------|---------|
| `containerlab-topologies` | Lab topologies as code — pinned images, startup config validation |
| `batfish-validation` | Mathematical network analysis — BGP/OSPF/ACL/reachability |
| `network-testing-framework` | pytest + Containerlab + Batfish — unit/integration/contract |
| `config-diff-audit` | Config drift detection — normalization, volatile stripping |
| `config-sanitizer` | Config/log redaction — deterministic placeholders, topology preservation |
| `network-config-drift-detection` | Scheduled drift detection — collect → normalize → diff → alert → remediate |
| `forwardnetworks-nqe` | Forward Networks NQE — query modeled network state and preserve snapshot-aware evidence |
| `terraform-opa-policy` | OPA/Conftest policy-as-code for Terraform network resources — deny non-compliant plans before apply |
| `gh-actions-network-ci` | GitHub Actions CI for network config — lint, dry-run, unit/integration tests, policy gate |
| `cis-network-compliance` | CIS benchmark compliance scanning — pass/fail findings, remediation commands, drift tracking |

### Observability (1)
| Skill | Purpose |
|-------|---------|
| `network-observability-stack` | Prometheus/Grafana/Loki/Tempo — snmp_exporter, gnmic, PromQL alerts |

### Operations (4)
| Skill | Purpose |
|-------|---------|
| `gitops-network-automation` | ArgoCD/Flux for network config — Kustomize overlays, pre/post sync hooks |
| `network-device-onboarding` | Day-0: ZTP, creds, host-keys, verify — idempotent, rollback per stage |
| `network-change-runbooks` | Auditable change execution — pre-checks, approval gates, rollback, evidence |
| `asa-config-backup-restore` | Firewall config backup, verify, restore with rollback for Cisco ASA |

### Cisco NSO (5)
| Skill | Purpose |
|-------|---------|
| `nso-device-onboarding` | NSO device onboarding — authgroups, NED assignment, sync-from |
| `nso-nano-services` | Reactive, multi-stage NSO services — plans, transitions, and recovery |
| `nso-python-fastmap` | Python-backed NSO services — FASTMAP callbacks and transactional mapping |
| `nso-service-package-development` | Cisco NSO service package design, implementation, and validation |
| `nso-xml-templates` | YANG-backed NSO services using XML templates |

### Utilities (11)
| Skill | Purpose |
|-------|---------|
| `ipam-subnetting` | Hierarchical CIDR allocation — VLSM, overlap detection, NetBox/TF seed data |
| `jinja2-network-templates` | Multi-vendor templates + filters — capability registry, StrictUndefined |
| `cli-tool-packaging` | Packaged Python CLIs — Typer/Click, Rich, dry-run, JSON output |
| `network-data-pipelines` | Pandas/Polars + Pydantic — normalization, cardinality control, quarantine |
| `network-rest-clients` | Typed REST clients — timeouts, retries, pagination, idempotency keys |
| `netbox-nautobot-api` | NetBox/Nautobot client — GraphQL bulk, pagination, dry-run |
| `nornir-napalm` | Fleet automation with Nornir — inventory layers, compare/commit/discard |
| `netconf-restconf-payloads` | XML/JSON payload construction — schema validation, Pydantic models |
| `pysnmp-automation` | SNMP v1/v2c/v3 async — GET/BULK/SET, traps, MIB resolution |
| `pyats-genie` | Cisco Genie parsers + AEtest — MetaParser, differential pre/post |
| `k8s-network-policy` | K8s CNI NetworkPolicy as code — namespace isolation, ingress/egress, deny-by-default, postcheck verification |
| `vault-network-secrets` | HashiCorp Vault for network credentials — KV v2, AppRole, transit encryption, audit logging |

---

## Skill Structure

```
skills/<skill-slug>/
├── SKILL.md              # Required: domain guidance, workflow, examples, validation
├── scripts/              # Optional: runnable helpers or validators
└── references/           # Optional: local fixtures, schemas, and supporting material
```

Not every skill has an offline validator: some require a live controller, device lab, or vendor-specific environment. Validate the collection's shared skill structure with:

```bash
python3 scripts/validate_skills.py
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

Skill documents can be read offline. Running their examples or validating
deployment behavior may require vendor tools, network devices, controllers,
or other external services. See
[references/open-source-local.md](references/open-source-local.md) for
recommended layout, dependency tiers, and quality gates.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidance on adding or updating
skills, citing technical claims, validating changes, and submitting pull
requests.

---

## License

MIT. Vendor names and product marks remain property of their respective owners.