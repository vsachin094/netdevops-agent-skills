---
name: network-device-onboarding
description: "Automate network device day-0/onboarding workflows: bootstrap (ZTP/DHCP), credential rotation, SSH host-key trust, config push, protocol verification, and inventory registration. Use this skill when new devices must be safely brought into management with audit trails and rollback."
license: MIT
compatibility: Python 3.10+; DHCP/TFTP/HTTP server for ZTP; Ansible/Netmiko/Scrapli for config push; NetBox/Nautobot/Infoblox for inventory; vendor onboarding APIs
---

# Network Device Onboarding (Intermediate)

Onboarding is a controlled lifecycle: discover → authenticate → trust → configure → verify → register. Each step must be auditable and reversible.

## Core Engineering Capabilities

- **ZTP/DHCP bootstrap** — DHCP options 66/67 or 43/60 for config script URL; iPXE/HTTP for vendor ZTP (Cisco ZTP, Arista ZTP, Juniper ZTP).
- **Credential rotation** — Replace default credentials with per-device or per-role credentials via config push; verify new credentials before disabling old.
- **SSH host-key trust** — Fetch and verify host keys (TOFU with pinned known_hosts or SSHFP DNS); store in known_hosts or inventory.
- **Configuration push** — Render and push baseline config (management IP, AAA, NTP, logging, SNMP, routing protocols) via NETCONF/RESTCONF/CLI.
- **Protocol verification** — Verify management reachability, AAA, NTP sync, syslog delivery, SNMP polling, BGP/OSPF adjacency.
- **Inventory registration** — Create/update device record in NetBox/Nautobot/Infoblox with interfaces, IPs, platform, site, role, and credentials reference.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never use default credentials in production; rotate on first boot.
- Verify SSH host key against SSHFP DNS or out-of-band source before accepting TOFU.
- Push baseline config in a single transaction (NETCONF candidate, RESTCONF candidate, or CLI checkpoint) with rollback on failure.
- Validate management reachability after config push before proceeding; fail fast if management IP changes break access.
- Distinguish onboarding failure types: unreachable, auth failure, config rejected, verification failed, inventory error.
- Make re-running onboarding idempotent: detect existing device, reconcile differences, report conflicts.
- Keep all credentials in Vault/secrets manager; never in scripts, logs, or inventory.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect device serial/MAC, platform, target site/role, management network, desired baseline config, credential policy, inventory system, and rollback procedure.

### Phase 2 (Implementation)

1. **ZTP/DHCP setup** — Configure DHCP options, host ZTP scripts on HTTP server, sign scripts if vendor supports it.
2. **Bootstrap config** — Minimal config to establish management connectivity (mgmt IP, gateway, AAA, SSH).
3. **Credential rotation** — Push new credentials, verify, then disable defaults.
4. **Host-key trust** — Fetch keys, validate against SSHFP or pinned list, store in known_hosts/inventory.
5. **Full baseline push** — Render full config from intent model, push via NETCONF/RESTCONF/CLI with validation.
6. **Verification** — Check reachability, AAA, NTP, syslog, SNMP, routing adjacency.
7. **Inventory registration** — Create device record with interfaces, IPs, platform, credentials reference.

### Phase 3 (Verification)

Test: new device (clean), existing device (reconcile), unreachable device (alert), auth failure (alert), config rejection (rollback), verification failure (alert + rollback), inventory conflict (report).

1. Simulate ZTP boot in lab → verify bootstrap config applied.
2. Run full onboarding against lab device → verify all steps pass.
3. Re-run onboarding → verify idempotent (no changes).
4. Inject failure at each step → verify proper error handling and rollback.

## Production Code / Template Example

### Input / Requirement

Provide device identity (serial/MAC), platform, site, role, management network, baseline config template, credential policy, inventory system API, and verification checks.

### Output / Generated Code

Return ZTP scripts, bootstrap config template, onboarding playbook/workflow, verification checks, inventory registration, and rollback procedures.

```python
# onboarding/workflow.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class OnboardingStage(Enum):
    ZTP_BOOTSTRAP = "ztp_bootstrap"
    CREDENTIAL_ROTATION = "credential_rotation"
    HOSTKEY_TRUST = "hostkey_trust"
    BASELINE_PUSH = "baseline_push"
    VERIFICATION = "verification"
    INVENTORY_REGISTRATION = "inventory_registration"

@dataclass
class OnboardingResult:
    device: str
    stage: OnboardingStage
    success: bool
    message: str
    rollback_needed: bool = False

def onboard_device(device_identity: dict, intent: dict) -> list[OnboardingResult]:
    results = []
    
    # Stage 1: ZTP Bootstrap (if new device)
    if not device_exists(device_identity):
        result = run_ztp_bootstrap(device_identity, intent)
        results.append(result)
        if not result.success:
            return results
    
    # Stage 2: Credential Rotation
    result = rotate_credentials(device_identity, intent)
    results.append(result)
    if not result.success:
        return results
    
    # Stage 3: Host-key Trust
    result = trust_hostkey(device_identity, intent)
    results.append(result)
    if not result.success:
        return results
    
    # Stage 4: Baseline Config Push
    result = push_baseline_config(device_identity, intent)
    results.append(result)
    if not result.success:
        return results
    
    # Stage 5: Verification
    result = verify_device(device_identity, intent)
    results.append(result)
    if not result.success:
        rollback_config(device_identity)
        return results
    
    # Stage 6: Inventory Registration
    result = register_inventory(device_identity, intent)
    results.append(result)
    
    return results
```

```python
# onboarding/ztp.py
def run_ztp_bootstrap(device_identity: dict, intent: dict) -> OnboardingResult:
    """Generate and serve ZTP bootstrap config."""
    platform = intent["platform"]
    
    if platform == "eos":
        config = render_template("ztp/eos.j2", {
            "mgmt_ip": intent["mgmt_ip"],
            "gateway": intent["gateway"],
            "username": intent["username"],
            "password_hash": intent["password_hash"],
            "ssh_key": intent["ssh_public_key"],
        })
    elif platform == "iosxe":
        config = render_template("ztp/iosxe.j2", {...})
    elif platform == "nxos":
        config = render_template("ztp/nxos.j2", {...})
    elif platform == "junos":
        config = render_template("ztp/junos.j2", {...})
    
    # Serve via HTTP (ZTP server)
    serve_ztp_config(device_identity["serial"], config)
    
    # Wait for device to fetch and apply (poll or webhook)
    if wait_for_device_online(intent["mgmt_ip"], timeout=300):
        return OnboardingResult(device=device_identity["name"], stage=OnboardingStage.ZTP_BOOTSTRAP, success=True, message="ZTP bootstrap complete")
    
    return OnboardingResult(device=device_identity["name"], stage=OnboardingStage.ZTP_BOOTSTRAP, success=False, message="ZTP timeout")
```

```python
# onboarding/verification.py
def verify_device(device_identity: dict, intent: dict) -> OnboardingResult:
    checks = [
        ("management_reachability", check_management_reachability),
        ("aaa_authentication", check_aaa),
        ("ntp_sync", check_ntp),
        ("syslog_delivery", check_syslog),
        ("snmp_polling", check_snmp),
        ("routing_adjacency", check_routing),
    ]
    
    failed = []
    for name, check_fn in checks:
        try:
            if not check_fn(device_identity, intent):
                failed.append(name)
        except Exception as e:
            failed.append(f"{name}: {e}")
    
    if failed:
        return OnboardingResult(
            device=device_identity["name"],
            stage=OnboardingStage.VERIFICATION,
            success=False,
            message=f"Verification failed: {', '.join(failed)}",
            rollback_needed=True
        )
    
    return OnboardingResult(device=device_identity["name"], stage=OnboardingStage.VERIFICATION, success=True, message="All verification checks passed")
```

```yaml
# onboarding/inventory_registration.yaml
# NetBox device creation
device:
  name: "{{ device_identity.name }}"
  device_type: "{{ intent.platform_model }}"
  device_role: "{{ intent.role }}"
  site: "{{ intent.site }}"
  platform: "{{ intent.platform }}"
  status: active
  tags: ["onboarded", "managed"]
  primary_ip4: "{{ intent.mgmt_ip }}/24"
  primary_ip6: null
  interfaces:
    - name: Management1
      type: 1000base-t
      mgmt_only: true
      ip_addresses: ["{{ intent.mgmt_ip }}/24"]
    - name: Ethernet1
      type: 100gbase-x-sr4
      description: "Uplink to spine"
  secrets_group: "network-device-credentials"
```

```bash
# scripts/onboard.sh
#!/bin/bash
set -euo pipefail

DEVICE_SERIAL="$1"
INTENT_FILE="$2"

# Load intent
INTENT=$(cat "$INTENT_FILE")

# Run onboarding
python -m onboarding.workflow --serial "$DEVICE_SERIAL" --intent "$INTENT_FILE" \
  --inventory-url "$NETBOX_URL" --inventory-token "$NETBOX_TOKEN" \
  --vault-addr "$VAULT_ADDR" --vault-token "$VAULT_TOKEN" \
  --output-dir "onboarding_logs/${DEVICE_SERIAL}"

# Check result
if [ $? -eq 0 ]; then
    echo "Onboarding successful for $DEVICE_SERIAL"
else
    echo "Onboarding failed for $DEVICE_SERIAL"
    exit 1
fi
```

```python
# tests/test_onboarding.py
import pytest
from unittest.mock import Mock, patch
from onboarding.workflow import onboard_device, OnboardingStage

def test_onboarding_success():
    device_identity = {"name": "leaf-01", "serial": "ABC123", "mac": "aa:bb:cc:dd:ee:ff"}
    intent = {
        "platform": "eos",
        "mgmt_ip": "192.0.2.11",
        "gateway": "192.0.2.1",
        "username": "netops",
        "role": "leaf",
        "site": "dc1",
    }
    
    with patch("onboarding.workflow.device_exists", return_value=False):
        with patch("onboarding.workflow.run_ztp_bootstrap") as mock_ztp:
            mock_ztp.return_value = Mock(success=True, stage=OnboardingStage.ZTP_BOOTSTRAP)
            with patch("onboarding.workflow.rotate_credentials") as mock_cred:
                mock_cred.return_value = Mock(success=True, stage=OnboardingStage.CREDENTIAL_ROTATION)
                with patch("onboarding.workflow.trust_hostkey") as mock_key:
                    mock_key.return_value = Mock(success=True, stage=OnboardingStage.HOSTKEY_TRUST)
                    with patch("onboarding.workflow.push_baseline_config") as mock_push:
                        mock_push.return_value = Mock(success=True, stage=OnboardingStage.BASELINE_PUSH)
                        with patch("onboarding.workflow.verify_device") as mock_verify:
                            mock_verify.return_value = Mock(success=True, stage=OnboardingStage.VERIFICATION)
                            with patch("onboarding.workflow.register_inventory") as mock_inv:
                                mock_inv.return_value = Mock(success=True, stage=OnboardingStage.INVENTORY_REGISTRATION)
                                
                                results = onboard_device(device_identity, intent)
                                
                                assert all(r.success for r in results)
                                assert len(results) == 6
```

## Validation, Linting & Testing Commands

- Test ZTP config rendering for each platform.
- Test credential rotation: old creds disabled, new creds work.
- Test host-key trust: TOFU with SSHFP, pinned keys, mismatch detection.
- Test baseline push: NETCONF candidate, RESTCONF candidate, CLI checkpoint/rollback.
- Test verification checks: reachability, AAA, NTP, syslog, SNMP, routing.
- Test inventory registration: create, update, conflict detection.
- Run `pytest tests/ -v` and `python3 scripts/validate_skills.py`.

## References

- [Arista ZTP](https://www.arista.com/en/support/technical-documentation/ztp)
- [Cisco IOS-XE ZTP](https://www.cisco.com/c/en/us/td/docs/ios-xml-ios/ztp/configuration/ztp-book.html)
- [Juniper ZTP](https://www.juniper.net/documentation/us/en/software/junos/ztp/)
- [NetBox REST API](https://netbox.readthedocs.io/en/stable/integrations/rest-api/)

## Offline Execution Contract

Generate ZTP configs, bootstrap templates, onboarding workflow, and verification checks locally. Without devices/DHCP/inventory, test config rendering, credential logic, and idempotency; mark live onboarding as unverified.

## Architecture & Technical Design Patterns

**Onboarding State Machine:**
```
NEW_DEVICE
    │
    ▼
ZTP_BOOTSTRAP ──► (timeout/fail) ──► ALERT
    │
    ▼
CREDENTIAL_ROTATION ──► (fail) ──► ROLLBACK_ZTP
    │
    ▼
HOSTKEY_TRUST ──► (mismatch) ──► ALERT + MANUAL_REVIEW
    │
    ▼
BASELINE_PUSH ──► (reject) ──► ROLLBACK_CREDS
    │
    ▼
VERIFICATION ──► (fail) ──► ROLLBACK_CONFIG
    │
    ▼
INVENTORY_REGISTRATION ──► (conflict) ──► REPORT_CONFLICT
    │
    ▼
ONBOARDED
```

**Idempotency Keys:**
- Device identity: serial number + MAC address
- Desired state hash: SHA256 of rendered baseline config
- Onboarding log: append-only JSONL with stage, timestamp, result, diff

**Credential Policy:**
- Per-device unique password (generated, stored in Vault)
- Per-role SSH key pair (device-type specific)
- TACACS+/RADIUS integration for AAA
- Certificate-based auth where supported (Junos, IOS-XE 17+)

**Rollback Strategy:**
| Stage | Rollback Action |
|-------|----------------|
| ZTP | Power cycle device, retry |
| Credentials | Re-enable defaults, disable new |
| Host-key | Remove from known_hosts |
| Baseline | NETCONF discard / CLI rollback |
| Verification | Rollback config, alert |
| Inventory | Delete created record |

**ZTP Server Requirements:**
- DHCP options 66 (TFTP server) + 67 (bootfile) or 43/60 (vendor-specific)
- HTTP server for config scripts (signed if vendor supports)
- Logging of all ZTP requests for audit
- Rate limiting per MAC/OUI

**Related Skills:**

- [network-config-drift-detection](network-config-drift-detection.md) — Post-onboarding compliance
- [ansible-role-creation](ansible-role-creation.md) — Ansible roles for baseline push
- [netmiko-core](netmiko-core.md) — CLI transport for vendors without NETCONF
- [ncclient-restconf](ncclient-restconf.md) — NETCONF/RESTCONF config push
- [network-testing-framework](network-testing-framework.md) — Test onboarding in lab
- [gitops-network-automation](gitops-network-automation.md) — Inventory as GitOps source