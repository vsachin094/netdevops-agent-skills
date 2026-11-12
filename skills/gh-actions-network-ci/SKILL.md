---
name: gh-actions-network-ci
description: "[Tier: Intermediate] GitHub Actions CI pipeline for network automation — lint configs, run dry-runs, execute unit and integration tests, validate Terraform plans, and gate merges on compliance checks. Use this skill when network config changes must pass automated checks before they reach production devices."
license: MIT
compatibility: GitHub Actions; Python 3.9+; Netmiko/Ansible/Terraform as needed; containerlab or lab devices for integration tests; repository with network config, playbooks, or Terraform modules
---

# GitHub Actions Network CI (Intermediate)

Run automated checks on network configuration changes in CI before they are merged or applied to production devices.

## Core Engineering Capabilities

- Lint network configs, Ansible playbooks, Terraform modules, and Python automation on every pull request.
- Run dry-runs (`ansible-playbook --check`, `terraform plan`, `netmiko --check`) to catch syntax and semantic errors without touching devices.
- Execute unit tests with mocked device connections (no lab required) and integration tests against lab devices (containerlab, cEOS, vSRX, etc.).
- Validate Terraform plans with OPA/Conftest policy-as-code before allowing apply.
- Gate merges: require all CI jobs to pass, require approvals for production environment changes, and block on critical severity findings.
- Generate compliance and test reports as pipeline artifacts; retain them for audit.
- Cache dependencies (Python packages, Terraform providers, Ansible collections) to speed up repeated runs.

## Architecture & Technical Design Patterns

```
pull request opened
        │
        ▼
   lint (ruff, ansible-lint, tflint, yamllint)
        │
        ▼
   dry-run (--check, terraform plan)
        │
        ▼
   unit tests (mocked devices)
        │
        ▼
   integration tests (lab devices, containerlab)
        │
        ▼
   policy gate (OPA/Conftest on tf plan)
        │
        ▼
   merge blocked unless all pass + approval
```

Separate fast jobs (lint, unit tests) from slow jobs (integration tests) so developers get quick feedback. Run integration tests only on PRs that touch device-affecting files (configs, playbooks, Terraform). Use matrix builds to test across multiple device types or platforms in parallel.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never store device credentials, API tokens, or vault tokens in GitHub repository secrets as plaintext without encryption; use GitHub Secrets with environment protection rules.
- Do not run `terraform apply` or Ansible `apply` directly from a pull request; apply only from a protected branch or manual dispatch with approval.
- Mask all command output that might contain secrets; use `::add-mask::` or GitHub job output masking.
- Require at least one reviewer for production environment changes; auto-merge is not allowed for infrastructure changes.
- Pin action versions (e.g., `actions/checkout@v4`) and dependency versions to avoid supply-chain surprises.
- Keep integration test devices in an isolated lab VLAN; never run destructive tests against production devices from CI.
- Fail the build on lint errors, test failures, and policy denials — do not allow bypass without a documented break-glass process.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Collect: repository layout (configs, playbooks, Terraform, Python automation), CI trigger events (push, pull_request, workflow_dispatch), device types for lab testing, secret sources (Vault, GitHub Secrets), approval requirements, and retention policy for artifacts.

### Phase 2 (Implementation)

Author the GitHub Actions workflow YAML with lint, dry-run, unit, integration, and policy jobs. Add environment protection rules for production. Configure artifact retention and secret masking.

### Phase 3 (Verification)

Open a test PR with a deliberate lint error and confirm the build fails. Open a PR with a compliant change and confirm it passes. Run integration tests against a lab device and confirm results are captured as artifacts.

### Input / Requirement

GitHub repository with network automation code, GitHub Actions enabled, lab devices or containerlab topology for integration tests, secret management (GitHub Secrets or Vault).

### Output / Generated Code

GitHub Actions workflow YAML, CI configuration, lab topology files, test fixtures, and documentation for on-call and break-glass procedures.

## Production Code / Template Example

```yaml
# .github/workflows/network-ci.yml (illustrative values; adjust paths and secrets)
name: Network CI

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

env:
  VAULT_ADDR: ${{ secrets.VAULT_ADDR }}
  VAULT_ROLE_ID: ${{ secrets.VAULT_ROLE_ID }}
  VAULT_SECRET_ID: ${{ secrets.VAULT_SECRET_ID }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install linters
        run: pip install ruff ansible-lint yamllint tflint
      - name: Lint Python automation
        run: ruff check scripts/ playbooks/
      - name: Lint Ansible playbooks
        run: ansible-lint playbooks/
      - name: Lint Terraform
        run: tflint --init && tflint
      - name: Lint YAML
        run: yamllint .

  dry-run:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install netmiko ansible
      - name: Ansible check mode
        run: ansible-playbook --check -i inventory/ playbooks/upgrade.yml
      - name: Terraform plan
        run: |
          cd terraform/
          terraform init
          terraform plan -out=tfplan

  unit-tests:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install test deps
        run: pip install pytest pytest-mock
      - name: Run unit tests
        run: pytest tests/unit/ -v

  integration-tests:
    needs: [dry-run, unit-tests]
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' && contains(github.event.pull_request.labels.*.name, 'integration')
    steps:
      - uses: actions/checkout@v4
      - name: Deploy lab topology
        run: containerlab deploy -t topology.clab.yml
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Teardown lab
        if: always()
        run: containerlab destroy -t topology.clab.yml

  policy-gate:
    needs: dry-run
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run OPA/Conftest
        run: conftest test -p policy terraform/tfplan.json

  deploy:
    needs: [integration-tests, policy-gate]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Apply changes (manual approval required)
        run: echo "Apply would run here after manual approval"
```

## Validation, Linting & Testing Commands

- `yamllint .github/workflows/network-ci.yml` — validate workflow YAML.
- `ansible-lint playbooks/` — lint Ansible content used in CI.
- `tflint` — lint Terraform modules.
- Run the workflow on a test PR and confirm each job passes/fails as expected.
- `python3 scripts/validate_skills.py` from the repository root.

## References

- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [Ansible lint documentation](https://ansible-lint.readthedocs.io/)
- [tflint documentation](https://github.com/terraform-linters/tflint)
- [containerlab documentation](https://containerlab.dev/)
- [Conftest documentation](https://www.conftest.dev/)

## Offline Execution Contract

Workflow authoring and linting can be done offline. Running CI jobs requires GitHub Actions runners and, for integration tests, lab devices or containerlab; mark integration test results unverified until run against a real lab.

## Related Skills

- [netmiko-core](../netmiko-core/SKILL.md) — Python automation linted and tested by this CI
- [ansible-netcli-playbooks](../ansible-netcli-playbooks/SKILL.md) — Ansible playbooks validated in dry-run jobs
- [tf-aws-networking](../tf-aws-networking/SKILL.md) — Terraform modules validated by plan and policy jobs
- [opa-terraform-network-policy](../opa-terraform-network-policy/SKILL.md) — policy gate for Terraform plans in CI
