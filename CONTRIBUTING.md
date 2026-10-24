# Contributing

Thanks for helping improve NetDevOps Agent Skills. Contributions can add a
skill, improve an existing workflow or example, fix an error, or improve the
repository's validation.

## Before you start

- Check the existing skills and open issues to avoid duplicating work.
- Keep changes focused on a clear networking task and its intended audience.
- Do not include credentials, private keys, customer configurations, or other
  sensitive or proprietary material.
- Use clear, direct language. Avoid claims that a skill has been tested or is
  supported unless the relevant documentation or recorded test supports that
  claim.

## Adding or updating a skill

Add a skill under `skills/<lowercase-hyphenated-slug>/SKILL.md`. Follow the
existing skill format and include:

- YAML frontmatter with `name`, `description`, `license`, and `compatibility`.
- Core capabilities and architecture or design patterns.
- Guardrails that explain assumptions, safety boundaries, and version-specific
  behavior.
- A phased workflow covering intake, implementation, and verification.
- A concrete input/requirement and output/example.
- Validation commands and a clear explanation of anything that requires a
  live device, controller, vendor tool, or other external environment.

Keep examples useful and runnable where practical. Mark illustrative values as
examples, not defaults. Include scripts or references only when they provide
useful, maintainable support for the skill; examples may live directly in
`SKILL.md` when that is clearer.

## Technical claims and sources

- Cite the applicable RFC or standards-body document for protocol requirements
  and numeric limits.
- Use official vendor documentation for platform-, hardware-, and
  release-specific behavior, support, and limits.
- Verify that each source supports the exact claim being made. A protocol
  description does not necessarily establish an operational default.
- Do not present an unsourced MTU, ASN range, timer, threshold, version
  requirement, compatibility matrix, or default as universal guidance.
- Describe unverified sample values as illustrative and ask for deployment
  context where a value must be selected.

## Validation

From the repository root, run:

```bash
python3 scripts/validate_skills.py
git diff --check
```

Also run any focused validator or tests provided by the skill you changed.
If a check needs a vendor environment or live network, state that limitation
and do not report the behavior as verified.

## Pull requests

- Explain the task or problem and summarize the changes.
- List validation commands and their results.
- Identify source references for standards- or vendor-specific claims.
- Call out any behavior that remains unverified or depends on a particular
  environment.
- Keep unrelated changes out of the pull request.

By contributing, you agree that your contributions are provided under the
repository's [MIT License](LICENSE).
