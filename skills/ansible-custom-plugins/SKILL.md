---
name: ansible-custom-plugins
description: "Develop tested Python Ansible modules, filter plugins, HttpApi plugins, and Netconf connection plugins with documented interfaces, check-mode support, and accurate idempotency. Use this skill when no supported collection module or plugin can express the required behavior."
license: MIT
compatibility: Ansible Core; Python 3.10+; AnsibleModule; pytest or ansible-test; target protocol SDK optional
---

# Ansible Custom Plugins (Expert)

Build the smallest extension that belongs in Ansible's execution and result model. A custom module is a public API and must behave correctly under check mode, diff mode, failure, and repeated execution.

## Core Engineering Capabilities

- Implement modules in `plugins/modules/`, filters in `plugins/filter/`, and HttpApi/Netconf connection plugins with documentation and tests.
- Return accurate `changed`, `failed`, `diff`, `before`, `after`, and `msg` fields and support check mode where meaningful.
- Use Ansible transport and module utilities rather than opening uncontrolled sessions or logging credentials.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Include `DOCUMENTATION`, `EXAMPLES`, and `RETURN` docstrings and a precise argument spec with choices, defaults, and secret flags.
- Set `supports_check_mode=True` only when check mode is implemented honestly; never mutate in check mode.
- Query current state, calculate desired change, apply only when needed, and return `changed=False` on a second run.
- Use `no_log`/secret parameters, validate external commands, and avoid shell injection or arbitrary path writes.
- Raise actionable failures and preserve protocol error context without exposing secrets. Use `ansible-test` sanity/unit/integration coverage.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Identify the plugin type, Ansible Core version, supported collections, input and return contracts, and the execution context. Read an existing plugin or module contract before inventing argument names or connection behavior.

### Phase 2 (Implementation)

Implement the smallest plugin that satisfies the contract, using Ansible module utilities, documented argument specs, check-mode behavior, and safe error messages. Keep transport, parsing, and business logic separable so each can be tested.

### Phase 3 (Verification)

Run unit tests with valid, invalid, check-mode, timeout, and authentication-failure cases. Exercise the plugin through ansible-test where available and inspect output for secrets, unstable return shapes, and non-idempotent changes.

1. Confirm no existing collection module or plugin is appropriate.
2. Define module contract and current/desired state behavior.
3. Implement, document, and unit-test check mode and idempotency.
4. Run `ansible-test` sanity and integration tests in a controlled target.

## Production Code / Template Example

### Input / Requirement

Provide the plugin type, target collection namespace, supported Ansible versions, argument schema, expected return structure, and representative success and failure inputs.

### Output / Generated Code

Return the plugin source, tests, documentation, and collection placement. Include the exact invocation used to exercise it and identify any behavior that still requires a live target.

```python
# plugins/modules/my_module.py
from ansible.module_utils.basic import AnsibleModule

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            desired=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        ),
        supports_check_mode=True,
    )
    current = read_state()
    changed = current != module.params["desired"]
    if changed and not module.check_mode:
        apply_change(module.params["desired"])
    module.exit_json(changed=changed, before=current, after=module.params["desired"])

def read_state():
    # Implement actual state reading
    return "current_value"

def apply_change(value):
    # Implement actual change
    pass

if __name__ == "__main__":
    run_module()
```

```python
# tests/test_my_module.py
import pytest
from ansible_collections.my_collection.plugins.modules import my_module

def test_check_mode_no_change():
    result = my_module.read_state()
    assert result == "current_value"
```

## Validation, Linting & Testing Commands

- Run `ansible-test sanity`, unit, and integration tests.
- Assert no mutation in check mode and no change on repeat.
- Test timeout, authentication, malformed input, partial mutation, and cleanup.
- Run `python3 scripts/validate_skills.py`.

## References

- [Ansible module development](https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_program_flow_modules.html)
- [Ansible test documentation](https://docs.ansible.com/projects/ansible/latest/dev_guide/testing.html)

## Offline Execution Contract

Custom modules and filters must run against mocked module utilities and fixtures. Without ansible-test or the target protocol, validate arguments, check mode, idempotency logic, and failure output without claiming integration success.

## Architecture & Technical Design Patterns

A custom module follows `argument_spec -> current state -> desired state -> diff -> optional mutation -> exit_json`. Secret arguments use `no_log`; choices, types, defaults, and mutually exclusive options belong in the spec. In check mode, return the predicted `changed` value and diff but perform no mutation. On normal execution, apply only when current and desired state differ, then re-read state where practical and return `before`, `after`, `changed`, and `diff`.

For filter plugins, keep functions pure and register them by name. For HttpApi/Netconf plugins, use Ansible's connection lifecycle, honor timeouts, support error classification, and never create an independent global session. Document `DOCUMENTATION`, `EXAMPLES`, and `RETURN`; run sanity, unit, and integration tests for success, invalid input, check mode, timeout, auth error, partial mutation, and second-run idempotency.