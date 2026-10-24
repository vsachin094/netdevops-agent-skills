---
name: network-protocols-as-code
description: "[Tier: Advanced] Generate vendor-neutral network protocol data models and reviewed configuration for Cisco IOS-XE, NX-OS, Arista EOS, and Juniper Junos across L2, IGP, BGP, VPN, QoS, and EVPN-VXLAN fabrics. Use this skill when translating an intent model into multi-vendor network configuration, design documentation, or pre-change validation artifacts."
license: MIT
compatibility: Python 3.10+; YAML or JSON; Jinja2 or an equivalent renderer; vendor CLI/API access only when explicitly authorized; optional Containerlab, Batfish, pyATS, or vendor parser toolchains
---

# Network Protocols as Code (Advanced)

Model protocol intent once, render vendor-specific syntax from that model, and
make the assumptions and invariants reviewable. The output is not merely a
CLI snippet: it is a version-controlled design artifact with policy,
validation, and rollback considerations.

## Core Engineering Capabilities

- Design L2 services: VLANs, 802.1Q trunks, MSTP, LACP, MLAG/vPC, and
  interface-level MTU and edge protections.
- Design IGPs: OSPF or IS-IS with area/level boundaries, router IDs,
  passive-interface policy, authentication, ECMP, and BFD where supported.
- Design BGP: eBGP/iBGP, address families, route policies, communities,
  maximum-prefix controls, local preference, MED, AS-path handling, and
  route-reflector policy.
- Design WAN and VPN intent: eBGP handoffs, IKEv2/IPsec profiles, QoS classes,
  and WireGuard peer definitions without embedding secrets.
- Design DC fabrics: EVPN-VXLAN leaf-spine underlay/overlay, VTEPs, VNIs,
  anycast gateways, route targets, MLAG/vPC roles, and fabric MTU.
- Render targeted configuration blocks for IOS-XE, NX-OS, EOS, and Junos;
  keep unsupported features explicit instead of silently approximating them.
- Produce a change manifest, pre-checks, post-checks, and a diff-friendly
  artifact suitable for a pull request or controlled deployment pipeline.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

### Evidence for requirements and values

- Cite the applicable RFC or standards-body document for protocol requirements,
  behavior, and numeric limits. Cite official vendor documentation for
  platform-, hardware-, and software-release-specific support or limits.
- Keep only values that the cited source actually supports. A source that
  describes packet format does not establish an operational default.
- Mark example values as illustrative and non-prescriptive. If a value cannot
  be verified, omit it or request the deployment-specific value instead of
  presenting it as guidance.

### Intent and vendor boundaries

- Start from a typed, vendor-neutral model. At minimum capture device role,
  platform, version, interfaces, peerings, address families, policy names,
  MTU, timers, and failure-domain metadata.
- Render only the platform features supported by the supplied release. If a
  vendor maps a concept differently, document the mapping in the output.
- Never mix configuration from different vendors in one device block. Group
  output by device and preserve deterministic ordering.
- Prefer generated policy names and stable keys over list indexes. A deleted
  peer must not cause unrelated policies or interfaces to be renumbered.

### Routing and failure detection

- Treat every eBGP session as deny-by-default until both import and export
  policy are explicitly attached. This implements the intent of RFC 8212.
- Apply maximum-prefix limits, peer descriptions, source interface/update
  source, authentication references, and an explicit address family to every
  BGP peer where the platform supports them.
- Use BFD only when the topology and platform support it. Validate that the
  peer, routing protocol, timers, detection multiplier, and authentication
  mode are compatible; do not blindly copy aggressive timers into a control
  plane.
- Define OSPF/IS-IS passive interfaces and area/level boundaries explicitly.
  Do not advertise a management or loopback interface by accident.
- Do not enable redistribution without an allow-list, route tags, and a
  loop-prevention policy. A default route is a deliberate intent, not a
  convenient fallback.

### Fabric, MTU, and security

- For VXLAN fabrics, calculate overhead and enforce an end-to-end jumbo MTU
  policy on underlay links, loopbacks, and relevant host-facing paths. Do not
  assume a universal jumbo-MTU value: derive the required path MTU from the
  encapsulation and packet format, then verify supported interface and system
  limits in the official documentation for each target platform and release.
- Model EVPN route targets, VNIs, VLAN-to-VNI mapping, anycast gateway MAC/IP,
  and multihoming or MLAG behavior as one coherent service. Do not generate a
  VNI without its tenant/VRF and bridge-domain relationship.
- Use modern IKEv2 profiles and authenticated encryption such as AES-GCM when
  the platform supports it. Put PSKs, private keys, and tunnel credentials in
  a secret manager or environment reference, never in the model or examples.
- Treat QoS as a complete policy: classification, marking, queueing,
  scheduling, shaping, and interface direction. Do not invent bandwidth
  percentages without an interface-speed assumption.

### Change safety

- Separate `intent`, `rendered`, `precheck`, `postcheck`, and `rollback`
  artifacts. A generated configuration is not evidence that the change is
  safe.
- Prefer candidate/commit, replace, or transactional APIs when available.
  If using CLI, include an explicit checkpoint or rollback plan appropriate
  to the platform.
- Never claim a configuration is valid based only on string rendering. Run
  vendor syntax checks, parser validation, a digital-twin test, or a dry-run
  where available. State what was and was not tested.
- Avoid operationally dangerous defaults such as unrestricted `permit ip any
  any`, unauthenticated routing adjacencies, disabled loop prevention, or
  management-plane exposure.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Capture the protocol intent, topology assumptions, timer and policy constraints, vendor targets, feature support, and the source-of-truth fields. Resolve ambiguous terms such as neighbor, area, ASN, or preference before modeling.

### Phase 2 (Implementation)

Represent the protocol as a vendor-neutral data model, then render or translate through explicit vendor adapters. Validate relationships such as peer endpoints, ASNs, areas, policies, and authentication before generating device syntax.

### Phase 3 (Verification)

Run schema validation, positive and negative topology fixtures, vendor render checks, and diff comparisons. Mark features that are modeled but not validated against a device or simulator.

1. **Clarify the design boundary.** Identify platforms/releases, device roles,
   topology, address plan, VRFs, protocol scope, target output, and whether
   the request is read-only, rendered-only, or authorized to deploy.
2. **Build the intent model.** Define shared fields first, then use vendor
   capability flags for platform-specific behavior. Use YAML or JSON with
   schemas and stable identifiers.
3. **Resolve dependencies.** Confirm underlay reachability before overlay
   configuration, interfaces before routing peers, VRFs before address
   families, and route policies before BGP activation.
4. **Render per platform.** Use Jinja2, a vendor API, or a structured
   configuration library. Keep templates thin: business decisions belong in
   the model or policy layer.
5. **Run invariant checks.** Check unique router IDs, unique VLAN/VNI IDs,
   symmetric MTU, peer address-family symmetry, matching ASN/roles, complete
   import/export policy, and no secret literals.
6. **Validate behavior.** Use platform parsers or syntax checks, then a
   Containerlab/Batfish/pyATS test where the topology is supported. Check
   reachability, BGP state, IGP adjacency, EVPN route types, and failure
   convergence expectations.
7. **Produce the change package.** Include source intent, rendered config,
   assumptions, validation output, pre-checks, post-checks, rollback steps,
   and an operator approval point. Do not perform deployment unless expressly
   authorized.

## Production Code / Template Example

### Input / Requirement

Provide the protocol, topology or adjacency data, vendor and software targets, policy requirements, timers, authentication references, and desired outputs.

### Output / Generated Code

Return the intent schema, example data, vendor-specific rendering or adapter code, validation errors, and a test matrix for supported protocol variants.


### Vendor-neutral intent

All numeric values in the examples below are illustrative, not operational
defaults. The IP addresses and ASNs use ranges reserved for documentation or
private use. No maximum-prefix number is prescribed: set it from the expected
route count, growth headroom, platform limits, and local routing policy.

```yaml
bgp:
  local_as: 65001
  router_id: 192.0.2.11
  neighbors:
    - name: spine-1
      address: 192.0.2.1
      remote_as: 65000
      address_families: [ipv4_unicast]
      import_policy: FABRIC-IN
      export_policy: FABRIC-OUT
      maximum_prefixes: ${VERIFIED_MAX_PREFIXES}
      bfd: true
```

### Illustrative IOS-XE IPv4-unicast excerpt

Replace `<verified-limit>` with the route limit established for the target
network and supported device release before using this configuration.

```text
router bgp 65001
 bgp router-id 192.0.2.11
 neighbor 192.0.2.1 remote-as 65000
 neighbor 192.0.2.1 description spine-1
 neighbor 192.0.2.1 fall-over bfd
 address-family ipv4
  neighbor 192.0.2.1 activate
  neighbor 192.0.2.1 maximum-prefix <verified-limit>
  neighbor 192.0.2.1 route-map FABRIC-IN in
  neighbor 192.0.2.1 route-map FABRIC-OUT out
 exit-address-family
```

The corresponding NX-OS, EOS, and Junos blocks may use different hierarchy
and policy attachment syntax. Preserve the same intent and explicitly call
out capabilities that do not map one-to-one.

### Required policy review

For every external BGP peer, the review artifact should answer:

```text
Peer: transit-a (illustrative review record)
Import policy: TRANSIT-IN (present, tested)
Export policy: TRANSIT-OUT (present, tested)
Maximum prefixes: chosen from measured route scale and verified platform limits
Default-originate: disabled
Route authentication: reference only; secret externalized
Rollback: remove peer activation, retain policy objects
```

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Validate model schema and render deterministically in CI.
- Run vendor-native syntax/config checks and inspect the rendered diff.
- Test eBGP policy behavior against RFC 8212 expectations: no explicit
  import/export policy means no accepted or advertised routes.
- Test BFD adjacency and failure behavior without assuming that a configured
  session is operationally established.
- For EVPN-VXLAN, verify underlay reachability, VTEP loopbacks, MTU,
  VLAN/VNI/VRF relationships, route targets, and anycast gateway symmetry.
- Run `terraform`/Ansible/NSO-specific validation only when those tools are
  the requested implementation target; do not imply one tool validates
  another tool's semantics.
- Check generated artifacts for secrets and redact device outputs before
  committing them.

## Authoritative References

- [RFC 7348: VXLAN](https://www.rfc-editor.org/rfc/rfc7348.html) — informational description of VXLAN encapsulation; it does not prescribe a universal underlay MTU.
- [RFC 5737: IPv4 Address Blocks Reserved for Documentation](https://www.rfc-editor.org/rfc/rfc5737.html)
- [RFC 6996: Autonomous System (AS) Reservation for Private Use](https://www.rfc-editor.org/rfc/rfc6996.html)
- [RFC 4271: A Border Gateway Protocol 4 (BGP-4)](https://www.rfc-editor.org/rfc/rfc4271.html)
- [RFC 8212: BGP Default Reject](https://www.rfc-editor.org/rfc/rfc8212.html)
- [RFC 2328: OSPF Version 2](https://www.rfc-editor.org/rfc/rfc2328.html)
- [RFC 1195: Use of OSI IS-IS for Routing in TCP/IP and Dual Environments](https://www.rfc-editor.org/rfc/rfc1195.html)
- [RFC 5880: Bidirectional Forwarding Detection](https://www.rfc-editor.org/rfc/rfc5880.html)
- [RFC 7432: BGP MPLS-Based Ethernet VPN](https://www.rfc-editor.org/rfc/rfc7432.html)
- [RFC 7296: Internet Key Exchange Protocol Version 2 (IKEv2)](https://www.rfc-editor.org/rfc/rfc7296.html)
- [RFC 4106: The Use of Galois/Counter Mode (GCM) in IPsec ESP](https://www.rfc-editor.org/rfc/rfc4106.html)
- [Cisco IOS-XE documentation](https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe/products-installation-guides-list.html) — consult the guide for the exact release and platform.
- [Arista EOS documentation](https://www.arista.com/en/support/toi) — verify feature support against the exact EOS release.
- [Juniper technical documentation](https://www.juniper.net/documentation/) — verify feature support against the exact Junos release.

## Offline Execution Contract

Use the vendor-neutral model, local templates, verified vendor documentation,
and captured fixtures. If a vendor tool or live device is unavailable, render
reviewable intent and validation artifacts, identify unsupported mappings,
and do not claim platform acceptance.

## Architecture & Technical Design Patterns

Minimum intent fields are `device`, `platform`, `version`, `role`, `interfaces`,
`vrfs`, `routing`, `peers`, `address_families`, `policies`, `mtu`, and
`credentials_ref`. Model BGP peers as objects, never as parallel lists:

```yaml
peer:
  id: spine-1
  address: 192.0.2.1
  local_as: 65001
  remote_as: 65000
  families: [ipv4_unicast, l2vpn_evpn]
  import_policy: FABRIC-IN
  export_policy: FABRIC-OUT
  max_prefixes: ${VERIFIED_MAX_PREFIXES}
```

For every peer, derive the following checks before rendering: local/remote
address-family symmetry, unique router IDs, valid ASNs, explicit import and
export policy for eBGP, maximum-prefix presence, and update-source reachability.
For an EVPN fabric, validate the chain `VLAN -> bridge-domain -> VNI -> VRF`
and require symmetric route-target import/export. Underlay links must have a
consistent MTU and IGP/BFD policy; overlay output is invalid if loopback
reachability is not modeled.

Renderer selection is deterministic: `platform + major_version + role` maps to
one template adapter. Unsupported features return a structured finding with
`feature`, `platform`, `version`, and `reason`; they must not silently fall
back to another vendor's syntax. Prechecks should verify interfaces, BGP/IGP
adjacency, MTU, and policy object existence; postchecks should verify the same
state plus intended route/EVPN changes.

## Platform and Release Compatibility

Do not rely on a generic feature/version matrix. Record the exact product,
hardware family, software release, feature, and relevant license, then verify
support and configuration behavior against the corresponding official vendor
documentation and release notes. Keep that source next to each compatibility
claim in generated design artifacts. If support cannot be verified, mark the
feature as unverified and do not render it as supported.

## Related Skills

- [jinja2-network-templates](../jinja2-network-templates/SKILL.md) — Template rendering for this intent model
- [containerlab-topologies](../containerlab-topologies/SKILL.md) — Lab validation of rendered configs
- [batfish-validation](../batfish-validation/SKILL.md) — Mathematical verification of rendered configs
- [network-change-runbooks](../network-change-runbooks/SKILL.md) — Pre/post checks for protocol changes
- [tf-aci-sdwan-meraki](../tf-aci-sdwan-meraki/SKILL.md) — Controller-based alternative for fabric intent
- [ansible-resource-modules](../ansible-resource-modules/SKILL.md) — Declarative Ansible alternative
