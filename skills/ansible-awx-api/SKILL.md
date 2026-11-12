---
name: ansible-awx-api
description: "[Tier: Intermediate] Automate AWX (Ansible Tower upstream) through its REST API — token authentication, inventory and host management, job template launches, job status polling, credential and project sync, and audit-ready evidence. Use this skill when network automation must trigger and monitor AWX job templates programmatically instead of only via the AWX web UI."
license: MIT
compatibility: AWX 21+ or Ansible Tower 3.8+; Python 3.9+; requests or awxkit library; AWX API access with token or basic auth; job templates, inventories, and credentials pre-created in AWX
---

# Ansible AWX API (Intermediate)

Control AWX through its REST API so network automation can launch job templates, manage inventories and credentials, and poll job status without manual web UI steps.

## Core Engineering Capabilities

- Authenticate to AWX via the REST API using token-based auth (preferred) or basic auth; rotate tokens on a schedule.
- Manage AWX inventory: create/update hosts, groups, and host variables for network devices through API calls.
- Launch job templates with extra variables (e.g., target devices, config versions) and capture the job ID for tracking.
- Poll job status until completion (successful, failed, canceled) and retrieve job output and host events.
- Manage AWX credentials (SSH keys, SSH passwords, vault credentials, API tokens) through the API for credential rotation.
- Trigger source control (SCM) inventory and project syncs so AWX uses the latest device inventory and playbook code.
- Produce audit evidence: API request/response logs, job IDs, launch times, completion status, and host-level results.

## Architecture & Technical Design Patterns

```
automation runner
        │
        ▼
   AWX API auth (token / basic)
        │
        ▼
   inventory sync → job template launch
        │
        ▼
   job status poll (interval + timeout)
        │
        ▼
   job output + host event retrieval
        │
        ▼
   audit evidence (job ID, status, results)
```

Keep AWX API base URL, token, and organization in environment variables or a secret store — never hardcode them. Use one API client session per run with proper timeout and retry settings. Prefix AWX inventory names with environment tags (e.g., `network-prod`, `network-staging`) so automation targets the right inventory.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never store AWX passwords, API tokens, or SSH private keys in source code, CI variables, or runner env vars as plaintext. Use a secret store (Vault, GitHub Secrets, AWX credentials) and inject at runtime.
- Do not launch job templates with unvalidated extra variables; sanitize and validate device lists, config versions, and other inputs before passing them to the API.
- Treat AWX job launches as state-changing operations; require a dry-run or preview mode where possible, and confirm the target inventory and job template before launching.
- Poll job status with bounded intervals and a maximum timeout; never poll indefinitely without a deadline.
- Redact sensitive output (passwords, keys, secrets) from job stdout before logging or storing as audit evidence.
- Confirm RBAC: the AWX API token must have only the permissions needed (inventory edit, job launch, job view) — not system administrator unless absolutely required.
- Test AWX API connectivity, auth, and job launch against a non-production AWX instance before pointing production automation at it.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: AWX base URL, auth method and credentials, organization, inventory names, job template names, credential names, target device lists, extra variables schema, poll interval and timeout, and evidence storage location.

### Phase 2 (Implementation)

Implement the AWX API client with auth, inventory CRUD, job template launch, job status polling, and output retrieval. Add input validation and secret redaction. Wire into the automation runner.

### Phase 3 (Verification)

Verify token authentication, inventory host CRUD, job template launch with extra vars, job status transitions (running → successful/failed), and job output retrieval. Test failure paths: invalid token, missing job template, unreachable devices, job cancellation.

### Input / Requirement

AWX instance with REST API access, authentication token or credentials, pre-created job templates, inventories, and credentials in AWX.

### Output / Generated Code

AWX API client code, inventory and job template launch scripts, job monitoring logic, audit evidence (job IDs, statuses, host results), and documentation for token rotation and RBAC.

## Production Code / Template Example

```python
# AWX API client for launching job templates (illustrative values)
import os
import time
import requests

AWX_URL = os.environ["AWX_URL"].rstrip("/")
AWX_TOKEN = os.environ["AWX_TOKEN"]

class AWXClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def launch_job_template(self, job_template_id: int, extra_vars: dict) -> int:
        url = f"{self.base_url}/api/v2/job_templates/{job_template_id}/launch/"
        resp = self.session.post(url, json={"extra_vars": extra_vars}, timeout=30)
        resp.raise_for_status()
        return resp.json()["job"]

    def poll_job(self, job_id: int, interval: int = 5, timeout: int = 600) -> dict:
        url = f"{self.base_url}/api/v2/jobs/{job_id}/"
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            job = resp.json()
            if job["status"] in ("successful", "failed", "canceled"):
                return job
            time.sleep(interval)
        raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

    def get_job_host_events(self, job_id: int) -> list:
        url = f"{self.base_url}/api/v2/jobs/{job_id}/host_summaries/"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("results", [])
```

## Validation, Linting & Testing Commands

- `python -m compileall` plus `ruff check` / `mypy` on AWX client modules.
- Unit tests with mocked `requests.Session`: successful auth, job launch returning job ID, job status transitions, host event retrieval, timeout on poll, invalid token handling.
- Integration test against a non-production AWX instance: launch a real job template, poll to completion, verify host summaries.
- Token rotation test: confirm expired token is rejected and new token works.
- `python3 scripts/validate_skills.py` from the repository root.

## References

- [AWX REST API documentation](https://awx.readthedocs.io/)
- [AWX API v2 job templates](https://docs.ansible.com/ansible-tower/latest/html/userguide/job_templates.html)
- [awxkit Python client](https://github.com/ansible/awxkit)
- [Ansible Tower API authentication](https://docs.ansible.com/ansible-tower/latest/html/userguide/api_authentication.html)

## Offline Execution Contract

API client authoring, auth flow design, and offline unit testing with mocked requests require no AWX instance. Live AWX auth, job launch, and job polling require an AWX or Ansible Tower instance; mark behavior unverified until tested against the target AWX version.

## Related Skills

- [ansible-netcli-playbooks](../ansible-netcli-playbooks/SKILL.md) — Ansible playbooks launched through AWX job templates
- [ansible-role-creation](../ansible-role-creation/SKILL.md) — roles that AWX job templates can reference
- [vault-network-secrets](../vault-network-secrets/SKILL.md) — secret store for AWX tokens and credentials
- [network-change-runbooks](../network-change-runbooks/SKILL.md) — change execution that can be triggered via AWX
