#!/usr/bin/env python3
"""Normalize Huawei VRP ``display`` output into structured pre/post-check baselines.

Supported commands (IPv4 unicast BGP, OSPFv2 neighbors and interface status only):

* ``display bgp peer``
* ``display ospf peer brief``
* ``display interface brief``

Volatile fields (message counters, OutQ, Up/Down timers, utilisation and error
counters) are dropped so that a baseline and a postcheck can be compared.

The parser fails closed: if the summary header is missing, a row cannot be
parsed, or the number of parsed BGP peers differs from the device's own
``Total number of peers`` line (or OSPF ``Total Peer(s)`` line), it raises ``VrpParseError`` instead of
returning a partial baseline.

Usage::

    normalize_vrp.py bgp-peer FILE                  # print normalized JSON
    normalize_vrp.py ospf-peer-brief FILE           # print normalized JSON
    normalize_vrp.py interface-brief FILE           # print normalized JSON
    normalize_vrp.py compare KIND BASELINE POST     # exit 1 on regression
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path


class VrpParseError(ValueError):
    """Raised when VRP output is incomplete or does not match the expected layout."""


_ROUTER_ID = re.compile(r"^\s*BGP local router ID\s*:\s*(\S+)", re.M)
_LOCAL_AS = re.compile(r"^\s*Local AS number\s*:\s*(\d+)", re.M)
_TOTALS = re.compile(
    r"Total number of peers\s*:\s*(\d+)\s+Peers in established state\s*:\s*(\d+)"
)
_BGP_HEADER = re.compile(r"^\s*Peer\s+V\s+AS\s+MsgRcvd\s+MsgSent\s+OutQ\s+Up/Down\s+State\s+PrefRcv\s*$", re.M)
_IF_HEADER = re.compile(r"^\s*Interface\s+PHY\s+Protocol\s+InUti\s+OutUti\s+inErrors\s+outErrors\s*$", re.M)
_OSPF_PROCESS = re.compile(r"^\s*OSPF Process (\d+) with Router ID (\S+)\s*$")
_OSPF_HEADER = re.compile(r"^\s*Area Id\s+Interface\s+Neighbor id\s+State\s*$")
_OSPF_TOTAL = re.compile(r"^\s*Total Peer\(s\)\s*:\s*(\d+)\s*$")
_OSPF_STATES = {"Down", "Attempt", "Init", "2-Way", "ExStart", "Exchange", "Loading", "Full"}
# Status token with an optional flag suffix, e.g. "up", "*down", "up(s)", "down(b)".
_STATUS = re.compile(r"^([*^#]?)(up|down)((?:\([A-Za-z]+\))*)$")


def parse_bgp_peer(text: str) -> dict:
    """Parse ``display bgp peer`` into ``{router_id, local_as, peers{ip: {...}}}``."""
    router_id = _ROUTER_ID.search(text)
    local_as = _LOCAL_AS.search(text)
    totals = _TOTALS.search(text)
    header = _BGP_HEADER.search(text)
    if not (router_id and local_as and totals and header):
        raise VrpParseError("display bgp peer: summary header or column header missing")

    peers: dict[str, dict] = {}
    for line in text[header.end():].splitlines():
        if not line.strip():
            continue
        fields = line.split()
        # Peer V AS MsgRcvd MsgSent OutQ Up/Down State PrefRcv
        if len(fields) != 9:
            raise VrpParseError(f"display bgp peer: unexpected row layout: {line.strip()!r}")
        peer, version, asn, _rcvd, _sent, _outq, _updown, state, pref_rcv = fields
        try:
            ipaddress.IPv4Address(peer)
        except ValueError as exc:
            raise VrpParseError(f"display bgp peer: unsupported peer address {peer!r}") from exc
        if not (version.isdigit() and asn.isdigit() and pref_rcv.isdigit()):
            raise VrpParseError(f"display bgp peer: non-numeric field in row: {line.strip()!r}")
        peers[peer] = {"remote_as": int(asn), "state": state, "prefixes_received": int(pref_rcv)}

    total, established = int(totals.group(1)), int(totals.group(2))
    if len(peers) != total:
        raise VrpParseError(
            f"display bgp peer: device reports {total} peers but {len(peers)} rows were parsed"
        )
    parsed_established = sum(1 for p in peers.values() if p["state"] == "Established")
    if parsed_established != established:
        raise VrpParseError(
            "display bgp peer: established count in header does not match parsed rows"
        )
    return {
        "router_id": router_id.group(1),
        "local_as": int(local_as.group(1)),
        "established": established,
        "peers": peers,
    }


def _dotted(value: str, what: str, line: str) -> None:
    try:
        ipaddress.IPv4Address(value)
    except ValueError as exc:
        raise VrpParseError(f"display ospf peer brief: bad {what} {value!r} in {line!r}") from exc


def parse_ospf_peer_brief(text: str) -> dict:
    """Parse ``display ospf peer brief`` into ``{process_id: {router_id, neighbors{...}}}``.

    Neighbors are keyed ``"<area>|<interface>|<neighbor id>"`` so the same
    neighbor reached over two links is checked per adjacency.
    """
    processes: dict[str, dict] = {}
    current: dict | None = None
    in_table = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or set(line) == {"-"} or line == "Peer Statistic Information":
            continue
        process = _OSPF_PROCESS.match(raw)
        if process:
            if current is not None and "total" not in current:
                raise VrpParseError("display ospf peer brief: process block without Total Peer(s) line")
            current = {"router_id": process.group(2), "neighbors": {}}
            processes[process.group(1)] = current
            in_table = False
            continue
        if current is None:
            raise VrpParseError(f"display ospf peer brief: content before process header: {line!r}")
        if _OSPF_HEADER.match(raw):
            in_table = True
            continue
        total = _OSPF_TOTAL.match(raw)
        if total:
            current["total"] = int(total.group(1))
            in_table = False
            continue
        if not in_table:
            raise VrpParseError(f"display ospf peer brief: unexpected line: {line!r}")
        fields = line.split()
        if len(fields) != 4:
            raise VrpParseError(f"display ospf peer brief: unexpected row layout: {line!r}")
        area, interface, neighbor, state = fields
        _dotted(area, "area id", line)
        _dotted(neighbor, "neighbor id", line)
        if state not in _OSPF_STATES:
            raise VrpParseError(f"display ospf peer brief: unknown state {state!r} in {line!r}")
        current["neighbors"][f"{area}|{interface}|{neighbor}"] = {"state": state}

    if not processes:
        raise VrpParseError("display ospf peer brief: no OSPF process header found")
    for pid, proc in processes.items():
        if "total" not in proc:
            raise VrpParseError(f"display ospf peer brief: process {pid} has no Total Peer(s) line")
        if proc["total"] != len(proc["neighbors"]):
            raise VrpParseError(
                f"display ospf peer brief: process {pid} reports {proc['total']} peers "
                f"but {len(proc['neighbors'])} rows were parsed"
            )
        del proc["total"]
    return processes


def _status(token: str, column: str, line: str) -> tuple[str, str, list[str]]:
    match = _STATUS.match(token)
    if not match:
        raise VrpParseError(f"display interface brief: bad {column} value {token!r} in {line!r}")
    prefix, state, flags = match.groups()
    return prefix, state, re.findall(r"\(([A-Za-z]+)\)", flags)


def parse_interface_brief(text: str) -> dict:
    """Parse ``display interface brief`` into ``{interface: {admin, phy, protocol, flags}}``."""
    header = _IF_HEADER.search(text)
    if not header:
        raise VrpParseError("display interface brief: column header missing")

    interfaces: dict[str, dict] = {}
    for line in text[header.end():].splitlines():
        if not line.strip():
            continue
        fields = line.split()
        # Interface PHY Protocol InUti OutUti inErrors outErrors
        if len(fields) != 7:
            raise VrpParseError(f"display interface brief: unexpected row layout: {line.strip()!r}")
        name, phy_raw, proto_raw = fields[:3]
        phy_prefix, phy, phy_flags = _status(phy_raw, "PHY", line.strip())
        _, protocol, proto_flags = _status(proto_raw, "Protocol", line.strip())
        interfaces[name] = {
            # "*down" = administratively down (shutdown); other prefixes keep admin up.
            "admin": "down" if phy_prefix == "*" else "up",
            "phy": phy,
            "phy_marker": phy_prefix or None,
            "protocol": protocol,
            "flags": sorted(set(phy_flags + proto_flags)),
        }
    if not interfaces:
        raise VrpParseError("display interface brief: no interface rows parsed")
    return interfaces


def compare_bgp(baseline: dict, post: dict) -> list[str]:
    """Every peer Established in the baseline must still exist and be Established."""
    problems = []
    for peer, before in baseline["peers"].items():
        after = post["peers"].get(peer)
        if after is None:
            problems.append(f"BGP peer {peer} missing after change")
        elif before["state"] == "Established" and after["state"] != "Established":
            problems.append(f"BGP peer {peer} {before['state']} -> {after['state']}")
        elif before["remote_as"] != after["remote_as"]:
            problems.append(f"BGP peer {peer} remote AS {before['remote_as']} -> {after['remote_as']}")
    return problems


def compare_ospf(baseline: dict, post: dict) -> list[str]:
    """Full adjacencies must stay Full; 2-Way (DROther pairs) must stay 2-Way or Full."""
    problems = []
    for pid, before in baseline.items():
        after = post.get(pid)
        if after is None:
            problems.append(f"OSPF process {pid} missing after change")
            continue
        for key, nbr in before["neighbors"].items():
            area, interface, neighbor = key.split("|")
            label = f"OSPF {pid} neighbor {neighbor} on {interface} (area {area})"
            now = after["neighbors"].get(key)
            if now is None:
                if nbr["state"] in {"Full", "2-Way"}:
                    problems.append(f"{label} missing after change")
            elif nbr["state"] == "Full" and now["state"] != "Full":
                problems.append(f"{label} Full -> {now['state']}")
            elif nbr["state"] == "2-Way" and now["state"] not in {"2-Way", "Full"}:
                problems.append(f"{label} 2-Way -> {now['state']}")
    return problems


def compare_interfaces(baseline: dict, post: dict) -> list[str]:
    """Every interface up/up in the baseline must still exist and be up/up."""
    problems = []
    for name, before in baseline.items():
        after = post.get(name)
        if after is None:
            problems.append(f"interface {name} missing after change")
            continue
        was_up = before["phy"] == "up" and before["protocol"] == "up"
        is_up = after["phy"] == "up" and after["protocol"] == "up"
        if was_up and not is_up:
            problems.append(
                f"interface {name} {before['phy']}/{before['protocol']} -> {after['phy']}/{after['protocol']}"
            )
    return problems


PARSERS = {
    "bgp-peer": parse_bgp_peer,
    "ospf-peer-brief": parse_ospf_peer_brief,
    "interface-brief": parse_interface_brief,
}
COMPARATORS = {
    "bgp-peer": compare_bgp,
    "ospf-peer-brief": compare_ospf,
    "interface-brief": compare_interfaces,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    for kind in PARSERS:
        p = sub.add_parser(kind, help=f"normalize {kind} output")
        p.add_argument("file", type=Path)
    cmp = sub.add_parser("compare", help="compare a baseline and a postcheck capture")
    cmp.add_argument("kind", choices=sorted(PARSERS))
    cmp.add_argument("baseline", type=Path)
    cmp.add_argument("post", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.action == "compare":
            parse = PARSERS[args.kind]
            problems = COMPARATORS[args.kind](
                parse(args.baseline.read_text(encoding="utf-8")),
                parse(args.post.read_text(encoding="utf-8")),
            )
            print(json.dumps({"passed": not problems, "problems": problems}, indent=2))
            return 1 if problems else 0
        print(json.dumps(PARSERS[args.action](args.file.read_text(encoding="utf-8")), indent=2, sort_keys=True))
        return 0
    except VrpParseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
