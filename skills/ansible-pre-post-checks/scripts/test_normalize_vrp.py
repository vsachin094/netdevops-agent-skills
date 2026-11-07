#!/usr/bin/env python3
"""Offline tests for normalize_vrp.py against sanitized VRP fixtures."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from normalize_vrp import (  # noqa: E402
    VrpParseError,
    compare_bgp,
    compare_interfaces,
    compare_ospf,
    parse_bgp_peer,
    parse_interface_brief,
    parse_ospf_peer_brief,
)

FIXTURES = HERE.parent / "fixtures" / "vrp"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class BgpPeerTests(unittest.TestCase):
    def test_baseline_is_normalized(self):
        result = parse_bgp_peer(load("bgp_peer_baseline.txt"))
        self.assertEqual(result["local_as"], 65001)
        self.assertEqual(result["established"], 3)
        self.assertEqual(
            result["peers"]["192.0.2.1"],
            {"remote_as": 65010, "state": "Established", "prefixes_received": 12},
        )

    def test_volatile_counters_do_not_cause_a_diff(self):
        baseline = parse_bgp_peer(load("bgp_peer_baseline.txt"))
        post = parse_bgp_peer(load("bgp_peer_postcheck_ok.txt"))
        self.assertEqual(compare_bgp(baseline, post), [])

    def test_named_peer_regression_is_reported(self):
        baseline = parse_bgp_peer(load("bgp_peer_baseline.txt"))
        post = parse_bgp_peer(load("bgp_peer_postcheck_peer_down.txt"))
        self.assertEqual(compare_bgp(baseline, post), ["BGP peer 192.0.2.2 Established -> Active"])

    def test_truncated_output_fails_closed(self):
        with self.assertRaises(VrpParseError):
            parse_bgp_peer(load("bgp_peer_truncated.txt"))

    def test_missing_header_fails_closed(self):
        with self.assertRaises(VrpParseError):
            parse_bgp_peer("Error: Unrecognized command found at '^' position.")


class OspfPeerBriefTests(unittest.TestCase):
    def test_baseline_is_normalized(self):
        result = parse_ospf_peer_brief(load("ospf_peer_brief_baseline.txt"))
        self.assertEqual(result["1"]["router_id"], "192.0.2.254")
        self.assertEqual(
            result["1"]["neighbors"]["0.0.0.0|GigabitEthernet0/0/1|192.0.2.1"], {"state": "Full"}
        )
        self.assertEqual(len(result["1"]["neighbors"]), 3)

    def test_documented_example_parses(self):
        # Layout of the example in Huawei WLAN AC V200R019C00 Command Reference, display ospf peer.
        doc = """
         OSPF Process 1 with Router ID 1.1.1.1
                  Peer Statistic Information
 -------------------------------------------------------------------
 Area Id         Interface                  Neighbor id      State
 0.0.0.0         Vlanif100       3.3.3.3          Full
 -------------------------------------------------------------------
 Total Peer(s):     1
"""
        result = parse_ospf_peer_brief(doc)
        self.assertEqual(result["1"]["neighbors"], {"0.0.0.0|Vlanif100|3.3.3.3": {"state": "Full"}})

    def test_unchanged_adjacencies_pass(self):
        baseline = parse_ospf_peer_brief(load("ospf_peer_brief_baseline.txt"))
        post = parse_ospf_peer_brief(load("ospf_peer_brief_postcheck_ok.txt"))
        self.assertEqual(compare_ospf(baseline, post), [])

    def test_regressions_are_named(self):
        baseline = parse_ospf_peer_brief(load("ospf_peer_brief_baseline.txt"))
        post = parse_ospf_peer_brief(load("ospf_peer_brief_postcheck_regression.txt"))
        self.assertEqual(
            compare_ospf(baseline, post),
            [
                "OSPF 1 neighbor 192.0.2.2 on GigabitEthernet0/0/2 (area 0.0.0.0) Full -> ExStart",
                "OSPF 1 neighbor 198.51.100.9 on Vlanif100 (area 0.0.0.1) missing after change",
            ],
        )

    def test_truncated_output_fails_closed(self):
        with self.assertRaises(VrpParseError):
            parse_ospf_peer_brief(load("ospf_peer_brief_truncated.txt"))

    def test_empty_output_fails_closed(self):
        with self.assertRaises(VrpParseError):
            parse_ospf_peer_brief("")


class InterfaceBriefTests(unittest.TestCase):
    def test_admin_down_and_flags(self):
        result = parse_interface_brief(load("interface_brief_baseline.txt"))
        self.assertEqual(result["GigabitEthernet0/0/3"]["admin"], "down")
        self.assertEqual(result["GigabitEthernet0/0/3"]["phy_marker"], "*")
        self.assertEqual(result["NULL0"]["protocol"], "up")
        self.assertEqual(result["NULL0"]["flags"], ["s"])

    def test_link_regression_is_reported_and_admin_down_ignored(self):
        baseline = parse_interface_brief(load("interface_brief_baseline.txt"))
        post = parse_interface_brief(load("interface_brief_postcheck.txt"))
        self.assertEqual(
            compare_interfaces(baseline, post),
            ["interface GigabitEthernet0/0/2 up/up -> down/down"],
        )

    def test_missing_header_fails_closed(self):
        with self.assertRaises(VrpParseError):
            parse_interface_brief("")


if __name__ == "__main__":
    unittest.main()
