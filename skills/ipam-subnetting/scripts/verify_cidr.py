#!/usr/bin/env python3
"""Verify a JSON IPAM plan for canonical CIDRs, containment, and overlap.

Input format:
{
  "aggregates": [{"name": "core", "prefix": "192.0.2.0/24", "vrf": "global"}],
  "allocations": [{"name": "web", "prefix": "192.0.2.0/26",
                   "parent": "core", "required_hosts": 50}]
}
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from pathlib import Path
from typing import Any


def conventional_usable_hosts(network: ipaddress._BaseNetwork, record: dict[str, Any]) -> int:
    """Return capacity under an explicit, conservative allocation policy."""
    if network.version == 6 or record.get("is_pool") or record.get("point_to_point"):
        return network.num_addresses
    return max(network.num_addresses - 2, 0)


def verify(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    aggregates = plan.get("aggregates", [])
    allocations = plan.get("allocations", [])
    if not isinstance(aggregates, list) or not isinstance(allocations, list):
        return ["aggregates and allocations must both be JSON arrays"]

    aggregate_by_name: dict[str, tuple[ipaddress._BaseNetwork, str]] = {}
    for index, item in enumerate(aggregates):
        if not isinstance(item, dict):
            errors.append(f"aggregates[{index}] must be an object")
            continue
        name, prefix = item.get("name"), item.get("prefix")
        if not isinstance(name, str) or not name:
            errors.append(f"aggregates[{index}].name is required")
            continue
        try:
            network = ipaddress.ip_network(prefix, strict=True)
        except (TypeError, ValueError) as exc:
            errors.append(f"aggregate {name!r} has invalid canonical prefix: {exc}")
            continue
        vrf = str(item.get("vrf", "global"))
        if name in aggregate_by_name:
            errors.append(f"duplicate aggregate name: {name}")
        aggregate_by_name[name] = (network, vrf)

    seen_names: set[str] = set()
    parsed: list[tuple[str, ipaddress._BaseNetwork, str]] = []
    for index, item in enumerate(allocations):
        if not isinstance(item, dict):
            errors.append(f"allocations[{index}] must be an object")
            continue
        name, prefix, parent = item.get("name"), item.get("prefix"), item.get("parent")
        if not isinstance(name, str) or not name:
            errors.append(f"allocations[{index}].name is required")
            continue
        if name in seen_names:
            errors.append(f"duplicate allocation name: {name}")
        seen_names.add(name)
        try:
            network = ipaddress.ip_network(prefix, strict=True)
        except (TypeError, ValueError) as exc:
            errors.append(f"allocation {name!r} has invalid canonical prefix: {exc}")
            continue
        if not isinstance(parent, str) or parent not in aggregate_by_name:
            errors.append(f"allocation {name!r} references unknown parent {parent!r}")
            continue
        aggregate, aggregate_vrf = aggregate_by_name[parent]
        vrf = str(item.get("vrf", aggregate_vrf))
        if network.version != aggregate.version:
            errors.append(f"allocation {name!r} changes address family from its parent")
        if not network.subnet_of(aggregate):
            errors.append(f"allocation {name!r} is outside parent {parent!r}")
        if vrf != aggregate_vrf:
            errors.append(f"allocation {name!r} VRF does not match parent {parent!r}")
        required = item.get("required_hosts")
        if required is not None:
            if not isinstance(required, int) or required < 0:
                errors.append(f"allocation {name!r}.required_hosts must be a non-negative integer")
            elif conventional_usable_hosts(network, item) < required:
                errors.append(f"allocation {name!r} lacks capacity for {required} hosts")
        parsed.append((name, network, vrf))

    for index, (left_name, left, left_vrf) in enumerate(parsed):
        for right_name, right, right_vrf in parsed[index + 1 :]:
            if left_vrf == right_vrf and left.version == right.version and left.overlaps(right):
                errors.append(f"allocations {left_name!r} and {right_name!r} overlap in VRF {left_vrf!r}")
    return errors


def self_test() -> int:
    valid = {"aggregates": [{"name": "core", "prefix": "192.0.2.0/24"}], "allocations": [
        {"name": "web", "prefix": "192.0.2.0/26", "parent": "core", "required_hosts": 50},
        {"name": "transit", "prefix": "192.0.2.64/30", "parent": "core", "required_hosts": 2, "point_to_point": True},
    ]}
    invalid = {"aggregates": [{"name": "core", "prefix": "192.0.2.0/24"}], "allocations": [
        {"name": "a", "prefix": "192.0.2.0/25", "parent": "core"},
        {"name": "b", "prefix": "192.0.2.64/26", "parent": "core"},
    ]}
    assert not verify(valid)
    assert verify(invalid)
    print("self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", type=Path, help="JSON plan file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.plan is None:
        parser.error("provide a plan JSON file or --self-test")
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to read JSON plan: {exc}", file=sys.stderr)
        return 2
    errors = verify(plan)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: verified {len(plan.get('allocations', []))} allocations across {len(plan.get('aggregates', []))} aggregates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
