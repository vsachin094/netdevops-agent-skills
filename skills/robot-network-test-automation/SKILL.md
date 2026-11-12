---
name: robot-network-test-automation
description: "[Tier: Intermediate] Build keyword-driven network test automation with Robot Framework — SSH/Netmiko keywords, config validation, connectivity checks, service verification, test data separation, and CI-friendly reporting. Use this skill when network teams need plain-language, maintainable test cases for pre/post-change validation and periodic compliance checks."
license: MIT
compatibility: Robot Framework 7+; Python 3.9+; robotframework-sshlibrary or robotframework-netmiko; requests library for REST checks; lab or target devices for test execution; Jenkins/GitHub Actions for CI reporting
---

# Robot Framework Network Test Automation (Intermediate)

Write keyword-driven network tests in plain language that verify device configuration, connectivity, and service health before and after changes, with CI-friendly reports.

## Core Engineering Capabilities

- Author test cases in Robot Framework DSL using keywords for device connection, command execution, config verification, and connectivity checks.
- Separate test data (variables, device credentials, expected values) from test logic using variable files and resource files.
- Use SSHLibrary or Netmiko-based keywords for CLI access to Cisco IOS/NX-OS, Juniper Junos, Arista EOS, and other network devices.
- Validate config drift by comparing actual device output against expected config snippets or baseline files.
- Run connectivity checks (ping, traceroute, port checks) and service verification (SSH, SNMP, REST API endpoints).
- Generate CI-friendly reports: Robot Framework output.xml, report.html, log.html with pass/fail counts and per-keyword execution times.
- Tag tests for selective execution (e.g., `pre-change`, `post-change`, `smoke`, `regression`) and run subsets in CI pipelines.
- Integrate with GitHub Actions or Jenkins so test results are published as pipeline artifacts.

## Architecture & Technical Design Patterns

```
test data (variables, resources)
              │
              ▼
    Robot Framework test cases
              │
              ▼
   SSHLibrary / Netmiko keywords
              │
              ▼
   device CLI / REST API calls
              │
              ▼
   assertions + keyword logs
              │
              ▼
   report.html + output.xml (CI artifact)
```

Use a directory structure with `tests/`, `resources/`, `variables/`, and `libraries/`. Store device credentials in variable files referenced from a secret store, never in test files. Use custom Python keyword libraries for complex validation logic that pure Robot keywords cannot express cleanly.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never hardcode device passwords, enable secrets, or API tokens in `.robot`, `.resource`, or `.py` files. Read from variable files loaded from environment variables or a secret store.
- Do not assert on fragile output that changes with device uptime or transient state; target stable fields (interface status, configured BGP neighbors, saved config lines).
- Use `Run Keyword If Expected Results` or explicit `Should Be Equal`/`Should Contain` assertions rather than relying on keyword exit codes alone.
- Set explicit timeouts on all device connections and command executions; never let a test hang indefinitely on an unreachable device.
- Clean up connections in test teardown (`Close Connection`) to avoid exhausting device session limits.
- Mark destructive tests clearly and gate them behind tags so they do not run in smoke or pre-change suites by accident.
- Treat Robot Framework as a test orchestrator, not a config management tool; use it to verify state, not to enforce desired config.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: target device inventory and OS types, credential source, test objectives (pre-change validation, post-change verification, periodic compliance), expected values for key checks, tag strategy, CI integration point, and report retention policy.

### Phase 2 (Implementation)

Create variable and resource files, write test cases using built-in and custom keywords, implement custom Python keyword libraries for complex checks, and wire tests into CI with tag-based selection.

### Phase 3 (Verification)

Run tests against lab devices and confirm pass/fail behavior matches expected state. Verify that a deliberate config drift is detected as a failure. Confirm reports are generated and published as CI artifacts. Test teardown closes all connections.

### Input / Requirement

Robot Framework installation, device inventory with credentials, test objectives and expected values, CI pipeline for report publishing.

### Output / Generated Code

Robot Framework test files (`.robot`), variable files, resource files, custom keyword libraries, CI pipeline configuration, and sample test reports.

## Production Code / Template Example

```robot
*** Settings ***
Documentation    Pre-change network validation for core switches
Library    SSHLibrary
Resource    resources/common_keywords.resource
Variables    variables/devices.yaml    variables/expected_values.yaml
Suite Setup    Connect To All Devices
Suite Teardown    Disconnect All Devices
Test Tags    pre-change

*** Test Cases ***
Verify SSH Access To All Devices
    [Documentation]    Confirm SSH is reachable on every target device
    [Tags]    smoke
    :FOR    ${device}    IN    @{DEVICES}
    \    ${status}=    Run Keyword And Return Status    Check Ssh Reachable    ${device}
    \    Should Be True    ${status}    SSH should be reachable on ${device}

Verify Interface Status
    [Documentation]    Confirm critical interfaces are up
    [Tags]    pre-change
    ${output}=    Execute Command    core-sw-01    show ip interface brief
    Should Contain    ${output}    GigabitEthernet1/0/1    up
    Should Contain    ${output}    GigabitEthernet1/0/2    up

Verify No Unused Services
    [Documentation]    CIS 1.1 - ensure service pad is disabled
    ${output}=    Execute Command    core-sw-01    show running-config | include service pad
    Should Be Empty    ${output}    service pad should be disabled
```

```python
# libraries/network_keywords.py (custom keyword library)
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword

class NetworkKeywords:
    def __init__(self):
        self.sshlib = BuiltIn().get_library_instance("SSHLibrary")
        self.connections = {}

    @keyword
    def connect_to_device(self, device_name, host, username, password):
        self.sshlib.open_connection(host, alias=device_name, timeout=10)
        self.sshlib.login(username, password)
        self.connections[device_name] = host

    @keyword
    def execute_command(self, device_name, command):
        self.sshlib.switch_connection(device_name)
        return self.sshlib.execute_command(command)

    @keyword
    def disconnect_all(self):
        for alias in list(self.connections.keys()):
            try:
                self.sshlib.switch_connection(alias)
                self.sshlib.close_connection()
            except Exception:
                pass
        self.connections.clear()
```

## Validation, Linting & Testing Commands

- `robot --lint tests/` — lint Robot Framework syntax.
- `python -m compileall libraries/` — compile-check custom keyword libraries.
- Run a smoke subset: `robot --include smoke --outputdir reports/ tests/` against lab devices.
- Verify report.html and output.xml are generated after a test run.
- `python3 scripts/validate_skills.py` from the repository root.

## References

- [Robot Framework User Guide](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.pdf)
- [Robot Framework SSHLibrary](https://github.com/robotframework/SSHLibrary)
- [Robot Framework Netmiko Library](https://github.com/nxp/robotframework-netmiko)
- [Robot Framework RequestsLibrary](https://github.com/MarketSquare/robotframework-requests)

## Offline Execution Contract

Test authoring, variable/resource file creation, and linting require no live devices. Test execution against real devices requires SSH/API access and a lab or maintenance window; mark device-specific behavior unverified until tested against target platforms.

## Related Skills

- [netmiko-core](../netmiko-core/SKILL.md) — SSH transport used by Robot Framework network keywords
- [cis-network-compliance](../cis-network-compliance/SKILL.md) — CIS compliance checks that can be automated as Robot Framework tests
- [gh-actions-network-ci](../gh-actions-network-ci/SKILL.md) — CI pipeline that can publish Robot Framework reports
- [config-diff-audit](../config-diff-audit/SKILL.md) — diff-based validation complementary to Robot Framework assertions
