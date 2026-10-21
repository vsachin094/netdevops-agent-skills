---
name: containerlab-topologies
description: "[Tier: Intermediate] Generate validated Containerlab topology YAML for FRRouting, Arista cEOS, Nokia SR Linux, Cisco images, and Linux containers with pinned images, startup configs, CI integration, and test inventories. Use this skill when building a repeatable local digital twin for network automation, CI tests, or pre-change validation."
license: MIT
compatibility: containerlab 0.50+; Docker 24+ or Podman 4+; node images and licenses supplied by user; Python 3.10+ for tooling; optional Ansible, pytest, Batfish
---

# Containerlab Topologies (Intermediate)

Make the lab a deterministic test fixture. Topology names, node identities, images, management addressing, endpoints, and startup configuration must be reviewable before deployment. Every topology must be CI-validated.

## Core Engineering Capabilities

- Generate `*.clab.yml` topologies with nodes, kinds, images, management networks, point-to-point endpoints, binds, startup configs, and env vars.
- Produce Ansible inventories, pytest fixtures, and Batfish snapshots from the same topology model.
- Support FRR, cEOS, SR Linux, Cisco IOS-XRv9k/NX-OSv, and Linux nodes where image availability and licensing are explicit.
- Pin image versions with digests; validate startup config syntax before deploy.
- Integrate with CI: `containerlab validate`, `containerlab deploy`, test execution, `containerlab destroy`, artifact collection.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- **Use unique lab/node names and deterministic management IPs;** avoid conflicts with host or existing lab networks. Management subnet must be `/24` or larger, non-overlapping with corporate/VPN ranges.
- **Every link has exactly two valid `node:interface` endpoints** and every node references a known kind/image. Validate with `containerlab validate` before deploy.
- **Pin image versions with digests** (`frrouting/frr@sha256:...`, `ghcr.io/nokia/srlinux@sha256:...`). Do not use `latest` or unpinned tags. Do not download proprietary images without license authorization.
- **Keep credentials and private configs out of topology files and CI logs.** Startup configs reference external secret paths or use runtime env vars.
- **Validate startup config syntax before deploy.** FRR: `vtysh -C -f startup.cfg`; SR Linux: `sr_cli -c "tools validate candidate"`; cEOS: `Cli -c "show running-config"` (in container).
- **Destroy only the named lab and preserve artifacts** required for troubleshooting (logs, inspect output, configs).
- **Resource limits:** Set `cpu`, `memory`, `cpuset` per node for CI runner stability. Default: 1 CPU, 1GB RAM per network node.
- **Kernel parameters:** Nodes requiring `sysctl` (FRR, SR Linux) must have `privileged: true` and `sysctls` in topology.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Confirm: lab purpose, node kinds and images (with digests), links, management network, startup configs, required capabilities (sysctl, privileged, KVM), resource budget, CI integration points, and test assertions. Verify every referenced image is available locally or explicitly mark as prerequisite.

### Phase 2 (Implementation)

1. **Topology model** — YAML/JSON with nodes, links, mgmt network, binds, env, sysctls, resource limits.
2. **Template renderer** — Jinja2 templates for `*.clab.yml`, Ansible inventory, pytest fixtures, Batfish snapshot input.
3. **Startup config validator** — per-kind syntax check before `containerlab deploy`.
4. **CI pipeline stage** — validate → deploy → wait ready → test → collect artifacts → destroy.
5. **Artifact collector** — `containerlab inspect`, `containerlab logs`, `containerlab exec`, configs to CI artifacts.

### Phase 3 (Verification)

Run topology validation, deploy in disposable lab when images exist, inspect links and interfaces, run test suite, destroy cleanly. Test: invalid link, missing image, duplicate node name, startup config syntax error, resource exhaustion, management IP conflict.

1. Define nodes, images (with digests), management subnet, links, startup config, tests.
2. Run `containerlab validate -t topology.clab.yml`.
3. Run `containerlab deploy -t topology.clab.yml --reconfigure`.
4. Wait for readiness: SSH (FRR, cEOS, SR Linux), gNMI (SR Linux), NETCONF (cEOS).
5. Run test suite: connectivity, protocol adjacency, config validation, Batfish analysis.
6. Collect artifacts: `containerlab inspect -t topology.clab.yml -f json`, logs, configs.
7. Run `containerlab destroy -t topology.clab.yml --cleanup`.

## Production Code / Template Example

### Input / Requirement

Provide the topology diagram, node images (with digests), link map, management requirements, startup configuration, and the assertions the lab must support.

### Output / Generated Code

Return the topology YAML, inventory or addressing data, validation command output, startup config validator, CI pipeline snippet, and a short list of checks that require the actual images.

### Topology Model (source of truth)

```yaml
# topology-model.yml
lab:
  name: spine-leaf-evpn
  mgmt_network: "clab-mgmt"
  mgmt_subnet: "172.20.20.0/24"
  mgmt_gateway: "172.20.20.1"
  domain: "clab.local"

nodes:
  - name: spine1
    kind: srl
    image: "ghcr.io/nokia/srlinux@sha256:abc123..."
    type: ixrd3
    license: "license.key"
    startup_config: "configs/spine1.cfg"
    binds:
      - "configs/spine1.cfg:/etc/opt/srlinux/startup.config"
    env:
      SRLINUX_LICENSE: "/etc/opt/srlinux/license.key"
    sysctls:
      net.ipv4.ip_forward: 1
      net.ipv6.conf.all.forwarding: 1
    resources:
      cpus: "2"
      memory: "2g"

  - name: leaf1
    kind: ceos
    image: "ceosimage:4.32.1F@sha256:def456..."
    startup_config: "configs/leaf1.cfg"
    binds:
      - "configs/leaf1.cfg:/mnt/flash/startup-config"
    env:
      CEOS: "1"
      EOS_PLATFORM: "ceoslab"
      SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT: "1"
      INTFTYPE: "eth"
    privileged: true
    resources:
      cpus: "1"
      memory: "1g"

  - name: leaf2
    kind: frr
    image: "frrouting/frr@sha256:ghi789..."
    startup_config: "configs/leaf2.frr"
    binds:
      - "configs/leaf2.frr:/etc/frr/frr.conf"
    sysctls:
      net.ipv4.ip_forward: 1
      net.ipv6.conf.all.forwarding: 1
    resources:
      cpus: "1"
      memory: "512m"

  - name: host1
    kind: linux
    image: "ubuntu:24.04@sha256:jkl012..."
    exec_commands:
      - "ip link set eth1 up"
      - "ip addr add 10.0.1.10/24 dev eth1"

links:
  - endpoints: ["spine1:e1-1", "leaf1:eth1"]
  - endpoints: ["spine1:e1-2", "leaf2:eth1"]
  - endpoints: ["leaf1:eth2", "host1:eth1"]
```

### Rendered Topology (Jinja2 → `spine-leaf-evpn.clab.yml`)

```yaml
name: spine-leaf-evpn
mgmt:
  network: clab-mgmt
  ipv4-subnet: 172.20.20.0/24
  ipv4-gw: 172.20.20.1
topology:
  defaults:
    kind: linux
  kinds:
    srl:
      image: ghcr.io/nokia/srlinux@sha256:abc123...
      type: ixrd3
      license: license.key
    ceos:
      image: ceosimage:4.32.1F@sha256:def456...
    frr:
      image: frrouting/frr@sha256:ghi789...
  nodes:
    spine1:
      kind: srl
      startup-config: configs/spine1.cfg
      binds:
        - configs/spine1.cfg:/etc/opt/srlinux/startup.config
      env:
        SRLINUX_LICENSE: /etc/opt/srlinux/license.key
      sysctls:
        net.ipv4.ip_forward: 1
        net.ipv6.conf.all.forwarding: 1
      resources:
        cpus: "2"
        memory: "2g"
    leaf1:
      kind: ceos
      startup-config: configs/leaf1.cfg
      binds:
        - configs/leaf1.cfg:/mnt/flash/startup-config
      env:
        CEOS: "1"
        EOS_PLATFORM: "ceoslab"
        SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT: "1"
        INTFTYPE: "eth"
      privileged: true
      resources:
        cpus: "1"
        memory: "1g"
    leaf2:
      kind: frr
      startup-config: configs/leaf2.frr
      binds:
        - configs/leaf2.frr:/etc/frr/frr.conf
      sysctls:
        net.ipv4.ip_forward: 1
        net.ipv6.conf.all.forwarding: 1
      resources:
        cpus: "1"
        memory: "512m"
    host1:
      kind: linux
      image: ubuntu:24.04@sha256:jkl012...
      exec:
        - ip link set eth1 up
        - ip addr add 10.0.1.10/24 dev eth1
  links:
    - endpoints: ["spine1:e1-1", "leaf1:eth1"]
    - endpoints: ["spine1:e1-2", "leaf2:eth1"]
    - endpoints: ["leaf1:eth2", "host1:eth1"]
```

### Startup Config Validator (per-kind)

```python
# scripts/validate_startup_configs.py
import subprocess
import sys
from pathlib import Path

VALIDATORS = {
    "frr": ["vtysh", "-C", "-f"],
    "srl": ["sr_cli", "-c", "tools validate candidate"],
    "ceos": ["Cli", "-c", "show running-config"],
}

def validate(kind: str, config_path: Path) -> tuple[bool, str]:
    if kind not in VALIDATORS:
        return True, f"No validator for {kind}, skipping"
    cmd = VALIDATORS[kind] + [str(config_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, "OK"
        return False, result.stderr
    except FileNotFoundError:
        return False, f"Validator not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "Validator timeout"

if __name__ == "__main__":
    # Called from CI: python validate_startup_configs.py topology-model.yml
    import yaml
    model = yaml.safe_load(Path(sys.argv[1]).read_text())
    failed = False
    for node in model["nodes"]:
        ok, msg = validate(node["kind"], Path(node["startup_config"]))
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {node['name']} ({node['kind']}): {msg}")
        if not ok:
            failed = True
    sys.exit(1 if failed else 0)
```

### CI Pipeline Stage (GitHub Actions)

```yaml
# .github/workflows/lab-test.yml
jobs:
  containerlab-test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Install containerlab
        run: |
          sudo bash -c "$(curl -sL https://get.containerlab.dev)"
      - name: Load images (if local)
        run: |
          docker load -i images/frr.tar
          docker load -i images/srl.tar
          # proprietary images loaded from secure storage
      - name: Validate topology
        run: containerlab validate -t spine-leaf-evpn.clab.yml
      - name: Validate startup configs
        run: python3 scripts/validate_startup_configs.py topology-model.yml
      - name: Deploy lab
        run: containerlab deploy -t spine-leaf-evpn.clab.yml --reconfigure
      - name: Wait for readiness
        run: |
          for node in spine1 leaf1 leaf2; do
            timeout 120 bash -c "until containerlab exec -t spine-leaf-evpn -n $node -- ssh -o StrictHostKeyChecking=no localhost 'echo ready'; do sleep 2; done"
          done
      - name: Run tests
        run: |
          pytest tests/lab/ -v --junitxml=results.xml
      - name: Collect artifacts
        if: always()
        run: |
          containerlab inspect -t spine-leaf-evpn.clab.yml -f json > inspect.json
          containerlab logs -t spine-leaf-evpn.clab.yml > lab.logs 2>&1
          mkdir -p configs
          for node in spine1 leaf1 leaf2; do
            containerlab exec -t spine-leaf-evpn -n $node -- cat /etc/frr/frr.conf > "configs/${node}.frr" 2>/dev/null || true
          done
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: lab-artifacts
          path: |
            inspect.json
            lab.logs
            configs/
            results.xml
          retention-days: 7
      - name: Destroy lab
        if: always()
        run: containerlab destroy -t spine-leaf-evpn.clab.yml --cleanup
```

### Ansible Inventory Generator

```python
# scripts/generate_inventory.py
import yaml
import json
from pathlib import Path

model = yaml.safe_load(Path("topology-model.yml").read_text())
mgmt_subnet = model["lab"]["mgmt_subnet"]
mgmt_gw = model["lab"]["mgmt_gateway"]

inventory = {"all": {"hosts": {}, "vars": {"ansible_user": "admin", "ansible_ssh_pass": "admin"}}}

for i, node in enumerate(model["nodes"]):
    # containerlab assigns mgmt IPs sequentially from subnet
    # This is a simplified generator; real impl uses containerlab inspect
    mgmt_ip = f"172.20.20.{i+2}"
    inventory["all"]["hosts"][node["name"]] = {
        "ansible_host": mgmt_ip,
        "ansible_network_os": node["kind"],
        "clab_kind": node["kind"],
    }

# Add groups by kind
for kind in set(n["kind"] for n in model["nodes"]):
    inventory["all"]["children"] = inventory["all"].get("children", {})
    inventory["all"]["children"][f"kind_{kind}"] = {
        "hosts": {n["name"]: {} for n in model["nodes"] if n["kind"] == kind}
    }

Path("inventory.yml").write_text(yaml.dump(inventory, sort_keys=False))
```

## Validation, Linting & Testing Commands

- **Topology validation:** `containerlab validate -t topology.clab.yml`
- **Startup config validation:** `python3 scripts/validate_startup_configs.py topology-model.yml`
- **Deploy test:** `containerlab deploy -t topology.clab.yml --reconfigure` (in CI with images)
- **Readiness test:** SSH/gNMI/NETCONF connectivity to all nodes
- **Test suite:** `pytest tests/lab/ -v` (connectivity, protocols, Batfish)
- **Artifact validation:** `containerlab inspect -f json` schema check
- **Destroy test:** `containerlab destroy --cleanup` leaves no containers/networks
- Run `python3 scripts/validate_skills.py` from repository root.

## References

- [Containerlab topology definitions](https://containerlab.dev/manual/topo-def-file/)
- [Containerlab validate](https://containerlab.dev/cmd/validate/)
- [Containerlab kinds](https://containerlab.dev/manual/kinds/)
- [FRRouting container](https://github.com/FRRouting/frr-docker)
- [Nokia SR Linux container](https://github.com/nokia/srlinux-container)
- [Arista cEOS-lab](https://www.arista.com/en/support/software-download)

## Offline Execution Contract

Validate topology structure, endpoints, and startup configs from local YAML without internet access. Without containerlab, Docker/Podman, or images, generate deployable topology artifacts and inventory but do not claim node boot, protocol convergence, or test execution.

## Architecture & Technical Design Patterns

**Minimum topology schema:**
```yaml
name: lab-name
mgmt:
  network: clab-mgmt
  ipv4-subnet: 172.20.20.0/24
topology:
  nodes:
    node-a:
      kind: linux
      image: image:tag@sha256:...
  links:
    - endpoints: ["node-a:eth1", "node-b:eth1"]
```

**Image pinning:** Always use `image@sha256:<digest>`. Store digests in `topology-model.yml`. CI loads images from tarballs or private registry — never pulls public `latest`.

**Management network:** Use `172.20.0.0/16` range for labs, allocate `/24` per concurrent CI job. `containerlab` assigns IPs sequentially; generator predicts them for inventory.

**Startup config per kind:**
- FRR: `/etc/frr/frr.conf` bind, validate with `vtysh -C -f`
- SR Linux: `/etc/opt/srlinux/startup.config` bind, validate with `sr_cli`
- cEOS: `/mnt/flash/startup-config` bind, `privileged: true`, env vars for licensing
- IOS-XRv9k: `/mnt/flash/startup-config`, `privileged: true`, KVM required

**Resource limits for CI:** Default 1 CPU / 1GB per node. SR Linux needs 2 CPU / 2GB. Set `cpuset` for deterministic scheduling on shared runners.

**Link validation:** Every endpoint `node:interface` must exist in node's interface list (containerlab validates this). For multi-homed links, use distinct interface names per endpoint.

**CI artifact hygiene:** Upload `inspect.json`, logs, configs, test results. Retention 7 days. Never upload images or license files.

## Vendor Version Compatibility

| Kind | Image Source | Tested Versions | Architecture | Resources | Licensing |
|------|--------------|-----------------|--------------|-----------|-----------|
| FRR | frrouting/frr | 8.5, 9.0, 9.1 | amd64/arm64 | 1 CPU, 512MB | Open source |
| SR Linux | ghcr.io/nokia/srlinux | 22.10, 23.3, 23.7 | amd64 | 2 CPU, 2GB | Requires license key |
| cEOS | arista/ceosimage | 4.32.1F, 4.33.0F | amd64 | 1 CPU, 1GB | Arista account |
| IOS-XRv9k | Cisco | 7.3, 7.8 | amd64 | 2 CPU, 4GB | Cisco contract |
| NX-OSv | Cisco | 9.3, 10.1 | amd64 | 2 CPU, 2GB | Cisco contract |
| Linux | ubuntu | 22.04, 24.04 | amd64/arm64 | 0.5 CPU, 256MB | Open source |

**Notes:**
- Always pin images with `@sha256:<digest>` in topology-model.yml
- SR Linux requires `sysctls` for IPv4/IPv6 forwarding
- cEOS requires `privileged: true` and specific env vars
- IOS-XRv9k requires KVM (`/dev/kvm` access)
- Proprietary images loaded from secure storage, never public registry

## Related Skills

- [netmiko-core](netmiko-core.md) — SSH transport for lab device interaction
- [nornir-napalm](nornir-napalm.md) — Fleet automation against lab devices
- [batfish-validation](batfish-validation.md) — Snapshot-based validation of lab configs
- [network-change-runbooks](network-change-runbooks.md) — Lab pre-change validation
- [network-protocols-as-code](network-protocols-as-code.md) — Render configs for lab deployment
- [nac-cicd-pipelines](nac-cicd-pipelines.md) — CI pipeline integration for lab tests