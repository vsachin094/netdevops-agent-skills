---
name: containerlab-topologies
description: "[Tier: Basic] Generate validated Containerlab topology YAML for FRRouting, Arista cEOS, Nokia SR Linux, Cisco images, and Linux containers with startup configs and test inventories. Use this skill when building a repeatable local digital twin for network automation or CI tests."
license: MIT
compatibility: containerlab; Docker/Podman; node images and licenses supplied by the user; Python optional
---

# Containerlab Topologies (Basic)

Make the lab a deterministic test fixture. Topology names, node identities,
images, management addressing, endpoints, and startup configuration must be
reviewable before deployment.

## Core Engineering Capabilities

- Generate `*.clab.yml` topologies with nodes, kinds, images, management
  networks, point-to-point endpoints, binds, and startup configs.
- Produce Ansible inventories and test metadata from the same topology model.
- Support FRR, cEOS, SR Linux, Cisco lab images, and Linux nodes where image
  availability and licensing are explicit.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use unique lab/node names and deterministic management IPs; avoid conflicts
  with host or existing lab networks.
- Every link has exactly two valid `node:interface` endpoints and every node
  references a known kind/image.
- Pin image versions and do not download proprietary images without license
  authorization.
- Keep credentials and private configs out of topology files and CI logs.
- Validate before deploy; destroy only the named lab and preserve artifacts
  required for troubleshooting.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Confirm the lab purpose, node kinds and images, links, management network, startup configs, required capabilities, and resource budget. Verify that every referenced image is available locally or explicitly mark it as a prerequisite.

### Phase 2 (Generation)

Generate a valid Containerlab topology with stable node names, explicit links, management addressing, and test inventory output. Keep secrets and proprietary images out of the topology repository.

### Phase 3 (Self-Verification)

Run topology validation, deploy in a disposable lab when images exist, inspect links and interfaces, and destroy the lab cleanly. Test an invalid link, missing image, and duplicate node name.

1. Define nodes, images, management subnet, links, startup config, and tests.
2. Run `containerlab validate -t topology.clab.yml`.
3. Deploy in an isolated runner, wait for readiness, run tests, and collect
   logs/configs as sanitized artifacts.

## Production Code / Template Example

### Input / Requirement

Provide the topology diagram, node images, link map, management requirements, startup configuration, and the assertions the lab must support.

### Output / Generated Code

Return the topology YAML, inventory or addressing data, validation command output, and a short list of checks that require the actual images.


```yaml
name: spineleaf
topology:
  nodes:
    spine1: {kind: linux, image: frrouting/frr:latest}
    leaf1: {kind: linux, image: frrouting/frr:latest}
  links:
    - endpoints: ["spine1:eth1", "leaf1:eth1"]
```

## Validation, Linting & Testing Commands

- Run the bundled schema/link checker, then `containerlab validate`.
- Test duplicate names/IPs, missing images, malformed endpoints, and startup
  config failures.
- Run `python3 scripts/validate_skills.py`.

## References

- [Containerlab topology definitions](https://containerlab.dev/manual/topo-def-file/)
- [Containerlab validate](https://containerlab.dev/cmd/validate/)

## Offline Execution Contract

Validate topology structure and endpoints from local YAML without internet access. Without containerlab, Docker/Podman, or images, generate deployable topology artifacts but do not claim node boot or protocol convergence.

## Architecture & Technical Design Patterns

The minimum topology schema is:

```yaml
name: lab-name
topology:
  nodes:
    node-a:
      kind: linux
      image: image:tag
  links:
    - endpoints: ["node-a:eth1", "node-b:eth1"]
```

Use unique lab/node keys, pinned images, explicit startup-config/file binds,
and a management network that cannot collide with the host. Generate links only
when both node/interface endpoints are known; for a leaf-spine fabric, derive
interface names from stable node IDs and validate that each point-to-point link
is emitted once. After deployment, wait for container health/SSH/API readiness
before running Ansible or protocol tests, and collect inspect output, logs,
and sanitized configs as CI artifacts.
