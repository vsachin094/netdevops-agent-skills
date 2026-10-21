---
name: nso-nano-services
description: "[Tier: Expert] Architect Cisco NSO Nano Services and LSA CFS-to-RFS packages with plan outlines, behavior trees, state callbacks, preconditions, post-actions, kickers, and zombie cleanup. Use this skill when provisioning is multi-stage, asynchronous, reactive, or requires explicit progress and self-healing state."
license: MIT
compatibility: Cisco NSO with Nano Services/Reactive FASTMAP support; YANG; Python/Java callbacks optional; compatible NED packages
---

# NSO Nano Services (Expert)

Model long-running provisioning as a declarative state machine. A Nano Service
is complete only when its plan reaches the intended final state and operational
postconditions are satisfied.

## Core Engineering Capabilities

- Define `ncs:plan-outline`, component types, deterministic states, behavior
  trees, selectors, multipliers, preconditions, post-actions, and kickers.
- Build asynchronous CFS-to-RFS and LSA workflows with explicit dependencies,
  progress reporting, backtracking, and zombie cleanup.
- Implement state callbacks/templates and verify plan transitions in tests.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Every component starts at `ncs:init` and ends at `ncs:ready`; use stable,
  past-tense custom state names and deterministic transitions.
- Keep plan synthesis in the behavior tree. Do not imperatively create Nano
  plan data from ordinary service callbacks.
- Preconditions must represent observable readiness, not arbitrary sleeps.
  Use kickers/subscribers for reactive progress and bound retry behavior.
- Design create and delete/backtracking paths together. Test zombie plans,
  partial failure, component removal, and make-before-break ordering.
- Keep component names and variables stable across re-evaluation; avoid
  identifiers derived from unordered data.
- Define LSA ownership and CFS/RFS boundaries explicitly, including error
  propagation and rollback expectations.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Ingestion & Validation)

Inspect the user-provided inputs, target versions, schemas, fixtures, inventory, and authorization boundary. Reject missing or ambiguous inputs before generation.

### Phase 2 (Generation)

Generate the requested artifact using the data model, implementation patterns, and guardrails defined in this skill. Keep output deterministic, reviewable, and secret-safe.

### Phase 3 (Self-Verification)

Run the skill-specific examples, validators, linters, tests, dry-run, render, or plan checks available locally. Report skipped checks and never claim an external system was verified without access.

1. Define lifecycle stages, external readiness signals, components, and final
   success criteria.
2. Model plan outline and behavior tree, then implement per-state callbacks or
   templates.
3. Test create, pause, resume, failure, backtrack, delete, and re-deploy.
4. Inspect plan operational data and verify self-healing/reconciliation under
   repeated triggers.

## Production Code / Template Example

### Input / Requirement

Use the user’s stated target, supplied data, platform/version, and acceptance criteria. If the example below omits an environment-specific value, keep it as an explicit variable or placeholder.

### Output / Generated Code


```yang
ncs:component-type "svc:device-config" {
  ncs:state "ncs:init";
  ncs:state "svc:configured" {
    ncs:create { ncs:nano-callback; }
    ncs:pre-condition { ncs:monitor "$SERVICE/device-ready"; }
  }
  ncs:state "ncs:ready";
}
```

Use a behavior tree to instantiate components and a real readiness monitor to
advance states; do not use fixed delays as a substitute for state.

## Validation, Linting & Testing Commands

At minimum, run `python3 scripts/validate_skills.py` from the repository root in addition to the domain-specific commands below.

- Assert all state transitions, plan statuses, preconditions, callbacks,
  post-actions, and backtracking outcomes in a lab NSO instance.
- Test failed and repeated kickers, partial LSA/RFS failure, service deletion,
  and zombie cleanup.
- Run `commit dry-run`, package compile, rollback tests, and the root validator.

## References

- [Cisco NSO Nano Services](https://nso-docs.cisco.com/guides/development/core-concepts/nano-services)
- [NSO Nano Services 6.2 guide](https://nso-docs.cisco.com/guides/nso-6.2/development/core-concepts/nano-services)
- [NSO lifecycle operations](https://nso-docs.cisco.com/guides/nso-6.5/operation-and-usage/operations/lifecycle-operations)

## Offline Execution Contract

Produce the plan outline, behavior tree, state table, and callback contracts from local schemas. Without NSO, test state-machine logic with fixtures and explicitly leave reactive execution, kickers, and zombie cleanup as lab gates.

## Architecture & Technical Design Patterns

Every component type should have `ncs:init` and `ncs:ready`; custom states sit
between them and should use past-tense names such as `requested`, `configured`,
or `verified`. A plan outline defines legal states and callbacks. A behavior
tree instantiates components from service input using selectors and
`multiplier/foreach` only when component identity is deterministic.

Model asynchronous readiness as a precondition that monitors an observable
leaf or plan state. Use kickers/subscribers to re-evaluate when that signal
changes; do not poll with arbitrary sleeps. Design deletion as backtracking:
new components may need to reach ready before old components are removed in a
make-before-break workflow. Test `init -> custom -> ready`, failure status,
retrigger, partial component failure, deletion/zombie retention, and final
cleanup. The `self` component is ready only when all required components and
post-actions are complete.
