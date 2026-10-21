---
name: nac-cicd-pipelines
description: "[Tier: Advanced] Generate GitHub Actions and GitLab CI pipelines for Network-as-Code, Ansible, NSO, and Terraform with lint, secret scan, digital-twin tests, dry-run/plan review, approval, deployment, and post-check stages. Use this skill when network changes need repeatable pull-request and release gates."
license: MIT
compatibility: GitHub Actions or GitLab CI; Python; Ansible; Terraform/OpenTofu; Containerlab/Batfish/NSO optional; secret scanner
---

# NaC CI/CD Pipelines (Advanced)

Make a network change pipeline prove progressively stronger properties before
deployment. A green syntax check is not a green production change.

## Core Engineering Capabilities

- Generate five-stage pipelines: lint/secret scan, digital twin, dry-run or
  plan, approval, deploy/postcheck.
- Publish rendered diffs and machine-readable evidence as review artifacts.
- Use protected environments, scoped credentials, concurrency controls, and
  rollback/postcheck jobs.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Never expose secrets in logs/artifacts; use short-lived environment secrets.
- Pin action/container/provider versions and use least-privilege identities.
- Require plan/dry-run output and human approval for production mutations.
- Serialize deployments per environment/state and cancel stale jobs safely.
- Treat failed postchecks as a release failure with a documented rollback path.
- Keep CI tests deterministic and do not connect to production from pull
  requests.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Map the pipeline stages, repository artifacts, approval gates, target environments, credentials boundaries, and rollback owner. Define what can run offline and which stage requires a lab, controller, or production approval.

### Phase 2 (Generation)

Generate a staged pipeline that lints, renders, validates in a twin or lab, creates a plan, pauses for approval, and deploys only the approved artifact. Pass immutable artifacts between stages rather than regenerating intent.

### Phase 3 (Self-Verification)

Run the pipeline with valid changes, schema failures, twin failures, approval rejection, deployment failure, and rollback. Confirm secrets are masked and every gate leaves evidence suitable for audit.

1. Lint and scan changed files.
2. Run offline parser/template/model and twin tests.
3. Generate plan/check/diff and comment evidence on the review.
4. Apply only in protected environment, then postcheck and publish outcome.

## Production Code / Template Example

### Input / Requirement

Provide the CI system, repository layout, change inputs, validation tools, approval rules, target environments, and rollback or break-glass procedure.

### Output / Generated Code

Return pipeline configuration, artifact contracts, gate conditions, environment variables without secrets, and a test matrix covering success and failure paths.


```yaml
jobs:
  plan:
    environment: staging
    concurrency: network-staging
    steps:
      - run: terraform plan -out=tfplan
      - run: terraform show -no-color tfplan > plan.txt
```

## Validation, Linting & Testing Commands

- Test fork/PR safety, secret masking, plan failure, approval denial, deploy
  timeout, concurrency, rollback, and postcheck failure.
- Validate workflow syntax and pin dependencies/actions.
- Run `python3 scripts/validate_skills.py`.

## References

- [GitHub Actions security](https://docs.github.com/en/actions/security-for-github-actions)
- [GitLab CI/CD](https://docs.gitlab.com/ee/ci/)
- [Terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan)

## Offline Execution Contract

Generate pipeline YAML and validate stage dependencies locally. Without CI, credentials, or labs, test workflow syntax and fixture-driven gates only; never claim deployment, approval, or postcheck execution.

## Architecture & Technical Design Patterns

Use five explicit stages with artifact handoff:

1. Lint, format, dependency and secret scan.
2. Offline parser/template/model tests plus Containerlab/Batfish where available.
3. Terraform plan, Ansible check/diff, NSO dry-run, or rendered network diff.
4. Protected environment approval with environment-scoped credentials.
5. Serialized deployment, postchecks, evidence publication, and rollback path.

Every job should identify changed scope, pin action/container versions, use
least-privilege secrets, and upload only redacted artifacts. Use concurrency
keys per environment/state to prevent simultaneous changes. Pull requests
must not connect to production. A postcheck failure must fail the release and
route to a documented rollback or operator decision rather than being marked
successful because deployment returned zero.
