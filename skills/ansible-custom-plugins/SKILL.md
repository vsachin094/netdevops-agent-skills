---
name: ansible-custom-plugins
description: "[Tier: Expert] Develop tested Python Ansible modules, filter plugins, HttpApi plugins, and Netconf connection plugins with documented interfaces, check-mode support, and accurate idempotency. Use this skill when no supported collection module or plugin can express the required behavior."
license: MIT
compatibility: Ansible Core; Python 3.10+; AnsibleModule; pytest or ansible-test; target protocol SDK optional
---

# Ansible Custom Plugins (Expert)

Build the smallest extension that belongs in Ansible's execution and result
model. A custom module is a public API and must behave correctly under check
mode, diff mode, failure, and repeated execution.

## Core Engineering Capabilities

- Implement modules in `plugins/modules/`, filters in `plugins/filter/`, and
  HttpApi/Netconf connection plugins with documentation and tests.
- Return accurate `changed`, `failed`, `diff`, `before`, `after`, and `msg`
  fields and support check mode where meaningful.
- Use Ansible transport and module utilities rather than opening uncontrolled
  sessions or logging credentials.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Include `DOCUMENTATION`, `EXAMPLES`, and `RETURN` docstrings and a precise
  argument spec with choices, defaults, and secret flags.
- Set `supports_check_mode=True` only when check mode is implemented honestly;
  never mutate in check mode.
- Query current state, calculate desired change, apply only when needed, and
  return `changed=False` on a second run.
- Use `no_log`/secret parameters, validate external commands, and avoid shell
  injection or arbitrary path writes.
- Raise actionable failures and preserve protocol error context without
  exposing secrets. Use `ansible-test` sanity/unit/integration coverage.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Confirm no existing collection module or plugin is appropriate.
2. Define module contract and current/desired state behavior.
3. Implement, document, and unit-test check mode and idempotency.
4. Run `ansible-test` sanity and integration tests in a controlled target.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```python
from ansible.module_utils.basic import AnsibleModule

module = AnsibleModule(
    argument_spec={"desired": {"type": "str", "required": True}},
    supports_check_mode=True,
)
current = read_state()
changed = current != module.params["desired"]
if changed and not module.check_mode:
    apply_change(module.params["desired"])
module.exit_json(changed=changed, before=current, after=module.params["desired"])
```

## Validation, Linting & Testing Commands

- Run `ansible-test sanity`, unit, and integration tests.
- Assert no mutation in check mode and no change on repeat.
- Test timeout, authentication, malformed input, partial mutation, and cleanup.
- Run `python3 scripts/validate_skills.py`.

## References

- [Ansible module development](https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_program_flow_modules.html)
- [Ansible module architecture](https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_program_flow_modules.html)
- [Ansible test documentation](https://docs.ansible.com/projects/ansible/latest/dev_guide/testing.html)

## Offline Execution Contract

Custom modules and filters must run against mocked module utilities and fixtures. Without ansible-test or the target protocol, validate arguments, check mode, idempotency logic, and failure output without claiming integration success.

## Architecture & Technical Design Patterns

A custom module follows `argument_spec -> current state -> desired state ->
diff -> optional mutation -> exit_json`. Secret arguments use `no_log`; choices,
types, defaults, and mutually exclusive options belong in the spec. In check
mode, return the predicted `changed` value and diff but perform no mutation.
On normal execution, apply only when current and desired state differ, then
re-read state where practical and return `before`, `after`, `changed`, and
`diff`.

For filter plugins, keep functions pure and register them by name. For
HttpApi/Netconf plugins, use Ansible's connection lifecycle, honor timeouts,
support error classification, and never create an independent global session.
Document `DOCUMENTATION`, `EXAMPLES`, and `RETURN`; run sanity, unit, and
integration tests for success, invalid input, check mode, timeout, auth error,
partial mutation, and second-run idempotency.
