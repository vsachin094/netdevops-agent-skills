---
name: ansible-ee-build
description: "Generate pinned Ansible Automation Platform execution environments with execution-environment.yml, requirements.yml, requirements.txt, and bindep.txt. Use this skill when Ansible network jobs must run reproducibly in AWX, AAP, ansible-navigator, or CI containers."
license: MIT
compatibility: ansible-builder v3; ansible-navigator; AWX/AAP; Python/pip; system package manager; vendor collections
---

# Ansible EE Build (Advanced)

An execution environment is a release artifact, not an unpinned dependency list. Make collection, Python, and system dependencies reproducible and inspectable.

## Core Engineering Capabilities

- Generate v3 execution environment definitions and pinned collection/Python/system dependency files for network automation.
- Include Netmiko, ncclient, pyATS, ntc-templates, Scrapli, cryptography, and provider libraries only when the workflow requires them.
- Produce build, scan, and navigator test instructions.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Pin or constrain collections, Python packages, and system libraries; review upgrades as dependency changes.
- Use a minimal base image and remove build-only artifacts where practical.
- Never bake credentials, SSH keys, vault passwords, or cloud tokens into the image or build context.
- Record ansible-builder, base image, collection, and Python versions.
- Test the built image with `ansible-navigator images`, syntax checks, and a disposable lab before publishing.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Record the Ansible Core, Python, collection, system-package, and base-image versions that the automation requires. Separate build-time dependencies from runtime credentials and target access.

### Phase 2 (Implementation)

Create a pinned execution-environment definition with a reproducible build context, minimal operating-system packages, and collection dependencies. Do not hide version constraints in an unreviewed install command.

### Phase 3 (Verification)

Build the image, inspect installed versions, run ansible-lint and a smoke playbook, and verify the same image works without network access after dependencies are cached. Test a missing collection and an incompatible Python version.

1. Inventory required modules, plugins, collections, and OS libraries.
2. Pin versions and generate dependency files.
3. Build and scan the image, then run a representative playbook offline.
4. Publish digest, SBOM/provenance, and upgrade notes.

## Production Code / Template Example

### Input / Requirement

Provide the controller or runner type, Ansible and Python versions, required collections, system packages, base image policy, and the smoke playbook or module set.

### Output / Generated Code

Return the execution-environment definition, dependency pins, build command, smoke test, and a short compatibility report for the target runner.

```yaml
# execution-environment.yml
version: 3
dependencies:
  galaxy: requirements.yml
  python: requirements.txt
  system: bindep.txt
additional_build_steps:
  prepend: |
    RUN python -m pip install --no-cache-dir --upgrade pip
```

```yaml
# requirements.yml
collections:
  - name: cisco.ios
    version: "6.0.0"
  - name: arista.eos
    version: "6.0.0"
  - name: cisco.nxos
    version: "6.0.0"
  - name: junipernetworks.junos
    version: "5.0.0"
  - name: ansible.netcommon
    version: "5.0.0"
  - name: ansible.utils
    version: "2.10.0"
```

```text
# requirements.txt
ansible-core==2.15.12
netmiko==4.3.0
ncclient==0.6.15
scrapli==2023.12.15
ntc-templates==2.4.0
pyyaml==6.0.1
jmespath==1.0.1
```

```text
# bindep.txt
git
ssh
openssh-client
ca-certificates
```

```bash
# Build and test
ansible-builder build -t ee-netops:v1 -f execution-environment.yml
ansible-navigator images
ansible-navigator run smoke.yml --mode stdout
```

## Validation, Linting & Testing Commands

- Build from a clean environment and test all required imports/collections.
- Scan image and dependencies for vulnerabilities and license policy.
- Verify runtime user, CA certificates, SSH tooling, and no secret layers.
- Run `python3 scripts/validate_skills.py`.

## References

- [ansible-builder documentation](https://ansible.readthedocs.io/projects/builder/en/latest/)
- [Ansible Navigator](https://ansible.readthedocs.io/projects/navigator/)
- [AAP execution environments](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/)

## Offline Execution Contract

Generate dependency manifests and inspect them locally. Without ansible-builder, container tooling, or registry access, validate YAML and pinning but do not claim the image builds or imports successfully.

## Architecture & Technical Design Patterns

Start from the playbook's actual imports: collection FQCNs belong in `requirements.yml`, Python imports in `requirements.txt`, and OS libraries or executables in `bindep.txt`. Keep versions pinned or bounded by a reviewed lock policy. The execution-environment definition should declare schema version, base image, dependency files, build steps, and runtime assumptions.

Build in a clean context, inspect the image, run `ansible-navigator` or `ansible-playbook --syntax-check`, import every required collection/plugin, and execute a representative offline fixture. Do not bake vault passwords, SSH keys, cloud credentials, or private package indexes into image layers. Record base-image digest, builder version, collection versions, Python version, and a security scan result with the published artifact.