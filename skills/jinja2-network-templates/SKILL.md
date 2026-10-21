---
name: jinja2-network-templates
description: "Build Jinja2 network configuration templates with strict data/template separation, reusable Python filters, and multi-vendor platform adapters. Use this skill when rendering deterministic configurations for IOS-XE, NX-OS, EOS, Junos, or other platforms from a single vendor-agnostic intent model."
license: MIT
compatibility: Python 3.10+; Jinja2 3+; PyYAML; Python ipaddress; pytest optional; vendor capability data
---

# Jinja2 Network Templates (Intermediate)

Keep templates concerned with presentation and YAML models concerned with intent. A rendered configuration must be deterministic, whitespace-safe, and rejected when required input is missing. Support multiple vendors through explicit platform adapters, not scattered conditionals.

## Core Engineering Capabilities

- Render common device stanzas (AAA, NTP, syslog, SNMP, VLANs, interfaces) from structured YAML/JSON data.
- Implement reusable Python filters for IP math, MAC formatting, interface compression, BGP peer derivation, and safe CLI quoting.
- Organize base templates, macros, includes, and vendor-specific adapter directories for interfaces, VLANs, routing, AAA, telemetry, and services.
- Select platform/version templates from validated device metadata and capability registry.
- Produce reviewable rendered files and machine-readable input models with deterministic ordering.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Configure `jinja2.StrictUndefined` so missing variables fail instead of producing `None`, empty commands, or malformed CLI.
- Keep secrets as references, not values. Never render passwords or keys into examples, logs, or committed artifacts.
- Use whitespace control deliberately (`{%-`, `-%}`) and test exact output; blank lines and indentation affect device parsers and diffs.
- Validate addresses, VLAN IDs, interface names, and enums before rendering.
- Keep source-of-truth data free of vendor CLI strings; vendor syntax belongs in adapter templates only.
- Use `{% include %}`, `{% extends %}`, and macros for composition; avoid copy/paste vendor templates that drift independently.
- Validate platform, version, required capabilities, and data schema before selecting a template. Unsupported combinations must fail clearly.
- Use stable ordering for interfaces, VLANs, peers, and policies so diffs are meaningful. Never use unordered set iteration.
- Do not hide semantic differences behind common variable names. Model them as capabilities or explicit vendor-specific fields.
- Render to files per device and platform; never concatenate different vendor configuration into one artifact.
- Filter functions must be side-effect free: no network calls, filesystem writes, global mutation, or time-dependent output.
- Type-check filter inputs and raise actionable errors for malformed IPs, VLANs, MACs, interfaces, or ASN values.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Identify the target vendors, platform versions, command/configuration modes, data schema, required defaults, whitespace rules, capability differences, and output artifacts. Separate values that belong in YAML/JSON from logic that belongs in templates and filters.

### Phase 2 (Implementation)

1. **Environment factory** — Create a strict Jinja environment with explicit undefined behavior, deterministic ordering, and registered filters.
2. **Filter library** — Implement pure Python filters with type checks, register them explicitly, and unit-test independently.
3. **Base templates** — Build shared macros and base templates for common patterns (loops, conditionals, whitespace handling).
4. **Vendor adapters** — Create platform-specific template directories with capability-aware branches.
5. **Capability registry** — Map `platform + major_version + feature` to supported/unsupported features.
6. **Renderer** — Select adapter by device metadata, validate capabilities, render with `StrictUndefined`.

### Phase 3 (Verification)

Render known-good and invalid data fixtures for each supported vendor, compare golden outputs, run syntax checks where available, test empty lists, missing required fields, capability gaps, and repeated rendering for stability.

1. Define vendor-neutral intent model and capability matrix.
2. Build shared macros and filter library with unit tests.
3. Implement one vendor adapter with golden fixtures.
4. Add additional vendors after confirming syntax and semantic mapping.
5. Render all supported fixtures, compare diffs, run vendor validation.

## Production Code / Template Example

### Input / Requirement

Provide canonical intent data, target vendors and versions, capability matrix, expected output differences, and platform validation tools available locally.

### Output / Generated Code

Return the shared model, vendor templates or adapters, capability declarations, filter library, golden outputs, and a matrix of supported and rejected features.

```text
project/
├── filters/
│   └── network.py          # Python filters: network_address, host_count, format_mac, quote_cli
├── templates/
│   ├── base/
│   │   └── interface.j2    # Shared macros
│   ├── iosxe/
│   │   └── interfaces.j2
│   ├── nxos/
│   │   └── interfaces.j2
│   ├── eos/
│   │   └── interfaces.j2
│   └── junos/
│       └── interfaces.j2
├── data/
│   └── intent.yml          # Vendor-agnostic intent
└── render.py               # Renderer with capability validation
```

```python
# filters/network.py
import ipaddress
import re
from typing import Union

def network_address(value: str) -> str:
    try:
        return str(ipaddress.ip_network(value, strict=False).network_address)
    except ValueError as exc:
        raise ValueError(f"invalid network {value!r}") from exc

def host_count(value: str, policy: str = "conventional") -> int:
    net = ipaddress.ip_network(value, strict=False)
    if net.version == 4:
        if net.prefixlen >= 31:
            return net.num_addresses
        if policy == "conventional":
            return max(net.num_addresses - 2, 0)
    return net.num_addresses

def format_mac(value: str) -> str:
    compact = value.replace(".", "").replace(":", "").replace("-", "").replace(" ", "").lower()
    if len(compact) != 12 or not all(c in "0123456789abcdef" for c in compact):
        raise ValueError(f"invalid MAC: {value}")
    return ":".join(compact[i:i+2] for i in range(0, 12, 2))

def compress_interface_range(interfaces: list[str]) -> str:
    if not interfaces:
        return ""
    return ", ".join(sorted(interfaces))

def quote_cli(value: str) -> str:
    if not value:
        return '""'
    if any(c in value for c in ' \t\n\r"\'`$'):
        return '"' + value.replace('"', '\\"') + '"'
    return value
```

```python
# render.py
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from filters import network as net_filters

CAPABILITIES = {
    "iosxe": ["lacp", "ospf", "bgp", "evpn", "mpls"],
    "nxos": ["lacp", "ospf", "bgp", "evpn", "vxlan"],
    "eos": ["lacp", "ospf", "bgp", "evpn", "vxlan"],
    "junos": ["lacp", "ospf", "bgp", "evpn", "mpls"],
}

def environment(path: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(path),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters.update({
        "network_address": net_filters.network_address,
        "host_count": net_filters.host_count,
        "format_mac": net_filters.format_mac,
        "compress_interface_range": net_filters.compress_interface_range,
        "quote_cli": net_filters.quote_cli,
    })
    return env

def render_device(device: dict, intent: dict, template_root: str) -> str:
    platform = device["platform"]
    version = device.get("version", "").split(".")[0]
    if platform not in CAPABILITIES:
        raise ValueError(f"Unsupported platform: {platform}")
    
    env = environment(template_root)
    
    required = intent.get("required_capabilities", [])
    missing = [c for c in required if c not in CAPABILITIES[platform]]
    if missing:
        raise ValueError(f"Platform {platform} missing capabilities: {missing}")
    
    template_name = f"{platform}/interfaces.j2"
    return env.get_template(template_name).render(device=device, intent=intent)
```

```jinja2
{# templates/iosxe/interfaces.j2 #}
{% for intf in intent.interfaces -%}
interface {{ intf.name }}
 description {{ intf.description | default('') }}
{% if intf.mode == 'trunk' -%}
 switchport trunk allowed vlan {{ intf.vlans | join(',') }}
 switchport mode trunk
{% elif intf.mode == 'access' -%}
 switchport access vlan {{ intf.vlan | default(1) }}
 switchport mode access
{% endif -%}
{% if intf.ipv4 -%}
 ip address {{ intf.ipv4 }}
{% endif -%}
{% endfor -%}
```

```jinja2
{# templates/junos/interfaces.j2 #}
{% for intf in intent.interfaces -%}
interfaces {
    {{ intf.name }} {
        description "{{ intf.description | default('') }}";
        {% if intf.mode == 'trunk' -%}
        unit 0 {
            family ethernet-switching {
                vlan {
                    members [ {{ intf.vlans | join(', ') }} ];
                }
            }
        }
        {% elif intf.mode == 'access' -%}
        unit 0 {
            family ethernet-switching {
                vlan {
                    members {{ intf.vlan | default(1) }};
                }
            }
        }
        {% endif -%}
        {% if intf.ipv4 -%}
        unit 0 {
            family inet {
                address {{ intf.ipv4 }};
            }
        }
        {% endif -%}
    }
}
{% endfor -%}
```

```yaml
# data/intent.yml
device:
  name: leaf-1
  platform: cisco_iosxe
  version: "17.12"
  capabilities: [lacp, ospf, evpn]
intent:
  required_capabilities: [evpn]
  interfaces:
    - name: GigabitEthernet1/0/1
      mode: trunk
      vlans: [10, 20]
      description: "Uplink to spine"
    - name: GigabitEthernet1/0/2
      mode: access
      vlan: 100
      ipv4: 192.0.2.1/30
```

## Validation, Linting & Testing Commands

- Run unit tests for filters independently of Jinja: `pytest tests/test_filters.py -v`
- Render every vendor fixture using strict undefined handling.
- Check golden output, syntax validation, stable ordering, and unsupported capability failures.
- Test empty optional sections, missing required fields, and invalid values for each vendor.
- Run `yamllint` on data files and `python3 scripts/validate_skills.py`.

## References

- [Jinja documentation](https://jinja.palletsprojects.com/en/stable/)
- [Jinja custom filters](https://jinja.palletsprojects.com/en/stable/api/#custom-filters)
- [Jinja template inheritance](https://jinja.palletsprojects.com/en/stable/templates/#template-inheritance)
- [Python `ipaddress`](https://docs.python.org/3/library/ipaddress.html)

## Offline Execution Contract

Use local templates, capability data, and golden outputs. If a vendor template or renderer is unavailable, generate the vendor-neutral model and an explicit unsupported-capability report rather than copying syntax from another platform.

## Architecture & Technical Design Patterns

**Environment Factory Pattern:**
```python
def environment(path: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(path),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )
```

**Filter Registration:**
```python
env.filters.update({
    "network_address": net_filters.network_address,
    "host_count": net_filters.host_count,
    "format_mac": net_filters.format_mac,
    "compress_interface_range": net_filters.compress_interface_range,
    "quote_cli": net_filters.quote_cli,
})
```

**Capability Registry:**
```python
CAPABILITIES = {
    "iosxe": ["lacp", "ospf", "bgp", "evpn", "mpls"],
    "nxos": ["lacp", "ospf", "bgp", "evpn", "vxlan"],
    "eos": ["lacp", "ospf", "bgp", "evpn", "vxlan"],
    "junos": ["lacp", "ospf", "bgp", "evpn", "mpls"],
}
```

**Template Selection:**
```python
template_name = f"{platform}/interfaces.j2"
rendered = env.get_template(template_name).render(device=device, intent=intent)
```

**Version Compatibility Matrix:**

| Platform | Version | EVPN | VXLAN | MPLS | SR-TE | Notes |
|----------|---------|------|-------|------|-------|-------|
| IOS-XE | 16.x | Partial | ✗ | ✓ | ✗ | EVPN 17.3+ |
| IOS-XE | 17.x | ✓ | ✗ | ✓ | ✗ | Multi-homing 17.6+ |
| NX-OS | 7.x | ✓ | ✓ | ✓ | ✗ | 7.0(3)I7+ |
| NX-OS | 9.x/10.x | ✓ | ✓ | ✓ | ✓ | Full feature |
| EOS | 4.25+ | ✓ | ✓ | ✗ | ✗ | No MPLS |
| EOS | 4.30+ | ✓ | ✓ | ✗ | ✗ | BGP ORF |
| Junos | 18.x | 19.1+ | ✗ | ✓ | ✗ | EVPN 19.1R1+ |
| Junos | 21.x | ✓ | ✗ | ✓ | 21.2+ | SR-TE |

**Related Skills:**

- [network-protocols-as-code](network-protocols-as-code.md) — Intent model that feeds these templates
- [containerlab-topologies](containerlab-topologies.md) — Lab validation of rendered configs
- [network-change-runbooks](network-change-runbooks.md) — Pre/post checks for template-driven changes
- [ansible-role-creation](ansible-role-creation.md) — Ansible roles that wrap template rendering
- [cli-tool-packaging](cli-tool-packaging.md) — Package renderer as internal CLI tool