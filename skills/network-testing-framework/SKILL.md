---
name: network-testing-framework
description: "Build a pytest-based network testing framework with Containerlab topologies, Batfish validation, and structured test fixtures for unit, integration, and contract testing. Use this skill when network automation needs repeatable, CI-integrated test suites with mocked and live device validation."
license: MIT
compatibility: Python 3.10+; pytest 7+; Containerlab 0.50+; Batfish (optional); pyATS/Genie (optional); vendor container images
---

# Network Testing Framework (Advanced)

Treat network tests as first-class code: versioned, reviewed, and run in CI. Separate unit tests (mocked), integration tests (lab), and contract tests (schema/behavior).

## Core Engineering Capabilities

- Define pytest fixtures for Containerlab topologies (FRR, cEOS, SR Linux, IOS-XRv9k) with automatic deploy/destroy.
- Implement Batfish snapshot tests for routing, reachability, ACL, and BGP session validation.
- Build contract tests that assert configuration schema, rendered output structure, and idempotency.
- Use pyATS/Genie for differential pre/post state validation in maintenance windows.
- Generate JUnit XML and structured JSON reports for CI dashboards.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never use production devices in CI; all tests run against lab or mocked fixtures.
- Pin container image digests in topology; never use `latest` tags.
- Isolate test state: each test gets a fresh topology or uses transactional rollback.
- Fail fast on parse warnings in Batfish; a parser warning affecting a query is a test failure.
- Mock external dependencies (DNS, NTP, AAA) in unit tests; use testcontainers for databases.
- Categorize tests with pytest markers: `unit`, `integration`, `contract`, `slow`, `requires_lab`.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Define the test pyramid: unit (mocked parsers/renderers), integration (Containerlab), contract (schema/behavior). Identify which components need live validation vs. static analysis.

### Phase 2 (Implementation)

1. **Fixture library** — `conftest.py` with topology fixtures, device connection fixtures, config fixtures.
2. **Unit tests** — Parser tests (TextFSM, TTP, regex), renderer tests (Jinja2), validator tests (IPAM, CIDR).
3. **Integration tests** — Containerlab topology deployment, protocol convergence, config push/pull.
4. **Contract tests** — JSON schema validation for config, state, and API responses.
5. **Differential tests** — Baseline snapshot → change → post snapshot → Batfish/pyATS diff.

### Phase 3 (Verification)

Run in CI: unit on every commit, integration on PR, contract on release. Measure flakiness, parallel execution time, and resource usage. Track test coverage for parsers, renderers, and validators.

1. `pytest -m unit` — fast, no external deps
2. `pytest -m integration` — requires Containerlab, images
3. `pytest -m contract` — schema validation
4. `pytest --junitxml=report.xml` — CI artifact

## Production Code / Template Example

### Input / Requirement

Provide topology definitions, test scenarios, expected behaviors, and CI pipeline integration points.

### Output / Generated Code

Return pytest fixture library, test modules, Containerlab topologies, Batfish questions, and CI pipeline configuration.

```python
# conftest.py
import pytest
import containerlab
import yaml

@pytest.fixture(scope="session")
def clab_topology(tmp_path_factory):
    """Deploy Containerlab topology for integration tests."""
    topology = """
    name: test-fabric
    topology:
      nodes:
        spine1:
          kind: srl
          image: ghcr.io/nokia/srlinux@sha256:...
        leaf1:
          kind: ceos
          image: ceosimage:4.32.1F@sha256:...
      links:
        - endpoints: ["spine1:e1-1", "leaf1:eth1"]
    """
    topo_file = tmp_path_factory.mktemp("clab") / "topology.clab.yml"
    topo_file.write_text(topology)
    
    clab = containerlab.ContainerLab(topo_file)
    clab.deploy()
    yield clab
    clab.destroy()

@pytest.fixture
def batfish_session():
    from pybatfish.client.session import Session
    bf = Session(host="localhost")
    yield bf

@pytest.fixture
def rendered_config():
    """Fixture for rendered config from jinja2-network-templates."""
    from jinja2_network_templates import render_device
    device = {"name": "leaf1", "platform": "eos", "version": "4.32"}
    intent = {"interfaces": [{"name": "Ethernet1", "mode": "trunk", "vlans": [10,20]}]}
    return render_device(device, intent, "templates")
```

```python
# tests/unit/test_jinja_filters.py
import pytest
from filters.network import network_address, host_count, format_mac

def test_network_address():
    assert network_address("192.0.2.10/32") == "192.0.2.10"
    assert network_address("2001:db8::1/64") == "2001:db8::"

def test_host_count():
    assert host_count("192.0.2.0/24") == 254
    assert host_count("192.0.2.0/31") == 2

def test_format_mac():
    assert format_mac("aabb.ccdd.eeff") == "aa:bb:cc:dd:ee:ff"
```

```python
# tests/integration/test_bgp_convergence.py
import pytest

@pytest.mark.integration
def test_bgp_established(clab_topology):
    """Verify BGP sessions establish after topology deploy."""
    spine = clab_topology.get_node("spine1")
    leaf = clab_topology.get_node("leaf1")
    
    # Wait for BGP convergence
    for _ in range(30):
        spine_bgp = spine.run_cli("show bgp summary")
        leaf_bgp = leaf.run_cli("show bgp summary")
        if "Estab" in spine_bgp and "Estab" in leaf_bgp:
            return
        time.sleep(2)
    pytest.fail("BGP did not converge")

@pytest.mark.integration
def test_interface_up(clab_topology):
    leaf = clab_topology.get_node("leaf1")
    output = leaf.run_cli("show interfaces status")
    assert "Ethernet1" in output and "up" in output
```

```python
# tests/contract/test_config_schema.py
import pytest
import jsonschema

CONFIG_SCHEMA = {
    "type": "object",
    "required": ["device", "platform", "version", "interfaces"],
    "properties": {
        "device": {"type": "string"},
        "platform": {"type": "string", "enum": ["iosxe", "nxos", "eos", "junos"]},
        "version": {"type": "string"},
        "interfaces": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "mode"],
                "properties": {
                    "name": {"type": "string"},
                    "mode": {"type": "string", "enum": ["access", "trunk"]},
                    "vlans": {"type": "array", "items": {"type": "integer"}},
                    "ipv4": {"type": "string", "format": "ipv4"},
                }
            }
        }
    }
}

@pytest.mark.contract
def test_config_schema(rendered_config):
    jsonschema.validate(instance=rendered_config, schema=CONFIG_SCHEMA)
```

```python
# tests/differential/test_batfish_diff.py
import pytest

@pytest.mark.integration
def test_no_unintended_reachability_change(batfish_session, clab_topology):
    """Batfish differential reachability test."""
    bf = batfish_session
    
    # Reference snapshot (pre-change)
    bf.init_snapshot("reference", network="test")
    
    # Apply change via automation
    # ... apply config change ...
    
    # Candidate snapshot (post-change)
    bf.init_snapshot("candidate", network="test")
    
    # Differential reachability
    diff = bf.q.differentialReachability(
        snapshot="candidate", reference_snapshot="reference"
    ).answer().frame()
    
    assert len(diff) == 0, f"Unintended reachability change: {diff}"
```

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest -m unit --junitxml=unit-report.xml
  
  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Install Containerlab
        run: sudo bash -c "$(curl -sL https://get.containerlab.dev)"
      - name: Load images
        run: docker load -i images/srl.tar && docker load -i images/ceos.tar
      - run: pytest -m integration --junitxml=integration-report.xml
  
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest -m contract --junitxml=contract-report.xml
```

## Validation, Linting & Testing Commands

- `pytest -m unit -v` — unit tests (no external deps)
- `pytest -m integration -v` — integration tests (requires lab)
- `pytest -m contract -v` — contract/schema tests
- `pytest --cov=src --cov-report=xml` — coverage for CI
- `python3 scripts/validate_skills.py`

## References

- [pytest documentation](https://docs.pytest.org/)
- [Containerlab testing](https://containerlab.dev/manual/testing/)
- [Batfish pybatfish](https://batfish.readthedocs.io/)
- [pyATS Genie](https://developer.cisco.com/docs/pyats/)

## Offline Execution Contract

Run unit and contract tests locally with mocked fixtures. Integration tests require Containerlab, Docker, and vendor images. Without lab infrastructure, generate test scaffolding and mark integration behavior as unverified.

## Architecture & Technical Design Patterns

**Test Pyramid:**

```
         /\
        /  \  Contract (schema, behavior)
       /----\
      /      \ Integration (Containerlab, live devices)
     /--------\
    /          \ Unit (mocked, fast, isolated)
   /------------\
```

**Fixture Hierarchy:**
```
conftest.py (session: topology, batfish)
  └── test_module.py (function: device_connection, config_fixture)
```

**Markers:**
```python
pytestmark = [
    pytest.mark.unit,           # No external deps
    pytest.mark.integration,    # Requires lab
    pytest.mark.contract,       # Schema validation
    pytest.mark.slow,           # > 30s
    pytest.mark.requires_lab,   # Needs Containerlab/images
]
```

**CI Integration:**
- Unit: every push, < 2 min
- Integration: PR, < 15 min (parallel topologies)
- Contract: release, < 5 min
- Reports: JUnit XML → dashboard, coverage → codecov

**Flakiness Mitigation:**
- Retry transient failures: `@pytest.mark.flaky(reruns=2, reruns_delay=5)`
- Timeouts: `@pytest.mark.timeout(60)`
- Resource cleanup: `try/finally` in fixtures, `clab.destroy()` in session teardown