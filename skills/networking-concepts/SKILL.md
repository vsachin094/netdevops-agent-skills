---
name: networking-concepts
description: "[Tier: Basic] Foundational networking concepts reference — OSI/TCP-IP model, IP addressing (IPv4/IPv6, VLSM, CIDR), routing and switching basics, common network devices, security fundamentals, and network management protocols. Use this skill when an agent needs a vendor-agnostic reference for networking fundamentals before applying any vendor-specific automation."
license: MIT
compatibility: Vendor-agnostic; applies to Cisco IOS/NX-OS, Juniper Junos, Arista EOS, Palo Alto PAN-OS, Linux networking, and cloud virtual networks; no specific software required
---

# Networking Concepts (Basic)

Vendor-agnostic networking foundations that every network automation skill assumes. Read this first for context on layers, addressing, routing, switching, devices, security, and management before applying any vendor-specific skill.

## Core Engineering Capabilities

- Explain the OSI 7-layer model and the TCP/IP 4-layer model, and map common protocols to their layers.
- Calculate IPv4 and IPv6 addressing: network/broadcast addresses, usable hosts, VLSM subnetting, CIDR aggregation, private vs public ranges, and reserved documentation blocks.
- Describe routing fundamentals: static vs dynamic routing, administrative distance, longest-prefix match, routing tables, and common protocols (OSPF, BGP, EIGRP, IS-IS, RIP).
- Describe switching fundamentals: MAC learning, VLANs, 802.1Q trunking, native VLAN, Spanning Tree Protocol (STP), EtherChannel, and Layer 2 vs Layer 3 boundaries.
- Identify common network devices and their roles: routers, Layer 2/Layer 3 switches, firewalls, load balancers, wireless controllers, and access points.
- Explain network security basics: ACLs, stateful firewalls, NAT, VPN tunnels (IPsec, GRE), AAA (RADIUS/TACACS+), and zero-trust principles.
- Explain network management protocols: SNMP, syslog, NTP, DHCP, DNS, ICMP, and their roles in monitoring and troubleshooting.
- Describe common WAN and data center fabrics: leased lines, MPLS, SD-WAN overlay, spine-leaf architecture, VXLAN, and EVPN basics.

## Architecture & Technical Design Patterns

```
Application (HTTP, DNS, DHCP, SNMP)
Transport (TCP, UDP)
Internet (IP, ICMP, BGP, OSPF)
Network Access (Ethernet, Wi-Fi, PPP)
```

```
Traffic flow: Client → Access Switch → Distribution Switch → Core Router → WAN/Internet
                                              │
                                          Firewall / Load Balancer
```

```
VLAN trunk: Access Port (untagged) ←→ Trunk Port (802.1Q tagged) ←→ Distribution/Layer 3
```

Use layered thinking when troubleshooting: verify Layer 1/2 (link, VLAN, trunk) before Layer 3 (IP, routing) before Layer 4+ (application, firewall policy).

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Do not assume all vendors use the same command syntax or default behavior; always confirm against the target device documentation.
- Never mix IPv4 and IPv6 addressing logic in the same subnet calculation; they are separate address families.
- A `/31` is a valid point-to-point link prefix in RFC 3021; do not apply the IPv4 `-2` usable-host rule to `/31` or `/32` links.
- Private RFC 1918 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) are not routable on the public Internet; NAT is required to reach external destinations.
- Documentation ranges (RFC 5737 IPv4, RFC 3849 IPv6) must be used in examples, never production addresses.
- Default gateway, DNS, and DNS search domains must be reachable before any upper-layer service can function.
- Spanning Tree blocks redundant Layer 2 paths; do not assume all physical links carry traffic.
- NAT breaks end-to-end traceability; account for translated addresses when troubleshooting across firewalls.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: the networking question or task, the vendor/platform involved, the OSI layer in scope, IP addressing scheme in use, routing protocol, VLAN design, security policy, and whether the task is read-only verification or a mutating change.

### Phase 2 (Implementation)

Map the requirement to the correct OSI layer and protocol. Apply addressing math (subnet, VLSM, CIDR), routing logic (longest-prefix match, administrative distance), or switching logic (VLAN, trunk, STP) as appropriate. Validate assumptions against device documentation.

### Phase 3 (Verification)

Confirm reachability step by step: Layer 1/2 link status → VLAN/trunk → IP connectivity (ping) → path trace (traceroute) → service port (TCP) → application response. Document each hop and any drop point.

### Input / Requirement

A networking question, task, or issue; vendor/platform context; IP addressing and topology information; and the OSI layer or protocol in scope.

### Output / Generated Code

A concept explanation, addressing calculation, routing/switching analysis, or troubleshooting path with identified layers, protocols, and drop points.

## Production Code / Template Example

```python
# IPv4 subnet calculation using Python ipaddress (illustrative values).
import ipaddress

def subnet_info(cidr: str) -> dict:
    net = ipaddress.ip_network(cidr, strict=True)
    return {
        "network": str(net.network_address),
        "broadcast": str(net.broadcast_address),
        "prefixlen": net.prefixlen,
        "total_addresses": net.num_addresses,
        "usable_hosts": max(net.num_addresses - 2, 0) if net.prefixlen < 31 else 0,
        "first_usable": str(list(net.hosts())[0]) if net.prefixlen < 31 else "N/A",
        "last_usable": str(list(net.hosts())[-1]) if net.prefixlen < 31 else "N/A",
        "is_private": net.is_private,
    }

# Example usage
# print(subnet_info("192.0.2.0/26"))
# Output: network=192.0.2.0, broadcast=192.0.2.63, usable_hosts=62
```

```python
# VLSM allocation check: does child fit inside parent without overlap?
import ipaddress

def is_contained(child_cidr: str, parent_cidr: str) -> bool:
    child = ipaddress.ip_network(child_cidr, strict=True)
    parent = ipaddress.ip_network(parent_cidr, strict=True)
    return child.subnet_of(parent)

# Example usage
# print(is_contained("192.0.2.0/27", "192.0.2.0/24"))  # True
# print(is_contained("10.0.0.0/27", "192.0.2.0/24"))   # False
```

## Validation, Linting & Testing Commands

- `python3 -c "import ipaddress; print(ipaddress.ip_network('192.0.2.0/24').num_addresses)"` — verify CIDR math basics.
- Run `python3 scripts/validate_skills.py` from the repository root when modifying this skill.
- Validate any subnet calculation against a known tool (ipcalc, sipcalc, or Terraform `cidrsubnet`).

## References

- [OSI model — Wikipedia](https://en.wikipedia.org/wiki/OSI_model)
- [TCP/IP model — Wikipedia](https://en.wikipedia.org/wiki/Internet_protocol_suite)
- [RFC 1918: Address Allocation for Private Internets](https://www.rfc-editor.org/rfc/rfc1918)
- [RFC 5737: IPv4 Address Blocks Reserved for Documentation](https://www.rfc-editor.org/rfc/rfc5737)
- [RFC 3849: IPv6 Address Prefix Reserved for Documentation](https://www.rfc-editor.org/rfc/rfc3849)
- [RFC 3021: Using /31 Prefixes on Point-to-Point Links](https://www.rfc-editor.org/rfc/rfc3021)
- [Python ipaddress module](https://docs.python.org/3/library/ipaddress.html)

## Offline Execution Contract

All concepts and Python examples work offline with no devices, controllers, or cloud access. Vendor-specific command behavior must be confirmed against the target device documentation; this skill is vendor-agnostic reference material, not a replacement for platform documentation.

## Related Skills

- [ipam-subnetting](../ipam-subnetting/SKILL.md) — deterministic IP allocation from these concepts
- [netmiko-core](../netmiko-core/SKILL.md) — applies Layer 2/3 concepts via SSH automation
- [cis-network-compliance](../cis-network-compliance/SKILL.md) — audits configs against these security concepts
- [robot-network-test-automation](../robot-network-test-automation/SKILL.md) — verifies these concepts with keyword tests
- [gh-actions-network-ci](../gh-actions-network-ci/SKILL.md) — CI gate that can enforce concept-based checks