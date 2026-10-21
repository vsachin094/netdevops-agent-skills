# Open-source and offline execution guide

This guide describes how to make the skill catalog useful to a local LLM,
developer workstation, or air-gapped CI runner.

## Recommended local layout

```text
tools/
├── venv/                    # pinned Python environment
├── vendor/                  # reviewed YANG modules and schemas
├── fixtures/                # sanitized CLI/API/device outputs
├── snapshots/               # Batfish/containerlab test inputs
└── images/                  # approved local lab image references
```

Keep credentials, private keys, raw production backups, and reversible scrub
maps outside this tree. Commit only sanitized fixtures and dependency lock
files.

## Dependency tiers

### Standard-library baseline

These workflows can run in a restricted Python environment:

- CIDR validation with `ipaddress`
- basic CLI regex parsing with `re`
- diff processing with `difflib` and `pathlib`
- deterministic secret/config scrubbing
- JSON/XML syntax validation

### Pinned open-source environment

Create a local lock file or wheelhouse for the packages used by a project:

```text
Jinja2
PyYAML
Pydantic
TextFSM
TTP
Nornir
NAPALM
pyang
Ansible Core and required collections
Terraform or OpenTofu
pybatfish
```

Do not install unpinned packages during an offline agent run. Build the
environment in a connected staging system, scan it, then transfer the wheel,
container, or package artifacts into the restricted environment.

### Platform adapters

For NetBox, Nautobot, cloud APIs, NSO, device images, and controller systems,
keep a local contract package containing:

- API/YANG schemas and version metadata
- sanitized request/response fixtures
- expected diffs and error responses
- simulator or containerlab topology where available
- a clear statement of what still requires live access

The agent can generate and validate against these artifacts without internet
access. A live deployment must still be separately authorized and tested.

## Offline quality gates

Every skill implementation should provide, where practical:

1. A deterministic local validator or parser test.
2. At least one positive and one negative fixture.
3. A documented dependency/version contract.
4. A dry-run, render, plan, or diff mode before mutation.
5. A clear error when a required external tool or platform is unavailable.

Offline tests prove syntax, schema, deterministic transformation, and modeled
behavior. They do not prove device-specific CLI acceptance, controller-side
authorization, hardware forwarding behavior, or vendor interoperability unless
the relevant simulator/lab is included.

## Licensing and redistribution

Use open-source dependencies according to their licenses and preserve notices.
Do not redistribute proprietary NSO NEDs, vendor device images, controller
schemas restricted by contract, or customer configurations. Reference those
artifacts by path or version and let users supply them locally.
