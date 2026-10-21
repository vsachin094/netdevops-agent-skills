# NetDevOps Agent Skills

## NetDevOps skills for AI coding agents

NetDevOps Agent Skills is an open-source catalog of production-oriented skills for
network automation, infrastructure as code, data-center fabrics, cloud
networking, observability, compliance, and SRE workflows.

Each skill is a self-contained directory with a SKILL.md file. It contains the
domain knowledge, implementation workflow, production guardrails, examples,
and validation commands an AI coding agent should follow. Some skills also
include deterministic Python or shell helpers.

The catalog is intended for:

- Claude Code and other Agent Skills-compatible hosts
- GitHub Copilot CLI, Copilot cloud agent, Copilot code review, and supported IDE agent modes
- Cursor and Continue through project rules or explicit file context
- Local LLMs and private coding agents with filesystem access
- Offline or air-gapped development when the required toolchain, schemas, fixtures, and lab artifacts are available locally

The skills provide instructions; they do not provide credentials, device
access, cloud permissions, vendor licenses, controllers, or network
connectivity.

## Project identity and naming

This project uses one public identity:

- Public name: **NetDevOps Agent Skills**
- Repository slug: `netdevops-agent-skills`
- Skill directories: lowercase, hyphenated slugs such as `ntc-textfsm`
- Skill metadata: the frontmatter `name` must exactly match its directory slug

The display name is used in documentation and licensing. The repository slug
is the URL-safe form used in clone commands and filesystem paths.

## Download the repository

### Git clone

Replace the URL with the repository URL where NetDevOps Agent Skills is published:

~~~bash
git clone <repository-url>
cd netdevops-agent-skills
~~~

### GitHub ZIP download

On GitHub, select **Code → Download ZIP**, extract the archive, and open the
extracted directory in your coding agent or copy the required skill directories
into the target project.

### Inspect a skill before installing it

~~~bash
sed -n '1,240p' skills/cli-regex/SKILL.md
find skills/cli-regex -maxdepth 2 -type f -print
~~~

Review the skill and any bundled scripts before allowing an agent to execute
commands. A skill is executable guidance when the host agent has shell or file
system permissions.

## Repository layout

~~~text
netdevops-agent-skills/
├── skills/
│   ├── cli-regex/
│   │   ├── SKILL.md                 # Required agent instructions
│   │   └── scripts/                 # Optional deterministic helpers
│   ├── ntc-textfsm/
│   │   └── SKILL.md
│   └── ...
├── references/
│   └── open-source-local.md         # Offline dependency and fixture guidance
├── scripts/
│   └── validate_skills.py           # Maintainer validation
├── LICENSE
└── README.md
~~~

SKILL.md is the only required file. Supporting scripts are kept inside the
skill that uses them and are referenced by that skill using relative paths.

## How a skill works

An agent uses the skill description to decide whether the skill is relevant.
You can also invoke or reference one explicitly. The normal flow is:

~~~text
User request
    │
    ▼
Agent identifies a matching skill
    │
    ▼
Agent reads skills/<slug>/SKILL.md
    │
    ├── validates inputs and dependencies
    ├── generates code, configuration, templates, or tests
    └── runs the documented checks before reporting completion
~~~

A skill is not a Python package and does not need to be installed with pip.
Install the external tools listed in the skill compatibility metadata only
when the requested workflow needs them.

## Install all skills into a project

Use this when the agent supports project-local skills under .agents/skills:

~~~bash
SOURCE_REPO="/path/to/netdevops-agent-skills"
mkdir -p .agents/skills
cp -R "$SOURCE_REPO"/skills/* .agents/skills/
~~~

Keep the directory structure unchanged:

~~~text
.agents/skills/<skill-slug>/SKILL.md
~~~

Do not flatten the files into one directory. The folder name and SKILL.md form
the skill identity, and helper scripts rely on the skill-local directory.

## Install selected skills

Installing only relevant skills reduces context and makes agent behavior easier
to review:

~~~bash
SOURCE_REPO="/path/to/netdevops-agent-skills"
mkdir -p .agents/skills
cp -R "$SOURCE_REPO"/skills/ipam-subnetting .agents/skills/
cp -R "$SOURCE_REPO"/skills/jinja2-config-base .agents/skills/
cp -R "$SOURCE_REPO"/skills/config-scrubber .agents/skills/
~~~

Useful combinations include:

- Network parsing: cli-regex → ntc-textfsm or ttp-parsers → config-diff-audit
- Infrastructure provisioning: ipam-subnetting → tf-vpc-foundations → tf-module-hardening
- Model-driven automation: yang-model-dev → pyang-xpath → netconf-restconf-payloads

These are suggestions, not mandatory dependencies. Read each skill's
compatibility and workflow sections before combining them.

## Agent-specific installation

There is no single filesystem location recognized by every coding agent. Keep
the original skill directory intact and use the native location for the host.

### Claude Code

Claude Code supports project skills in .claude/skills and personal skills in
~/.claude/skills. Project skills are available when Claude Code runs in that
repository; personal skills are available across projects.

~~~bash
SOURCE_REPO="/path/to/netdevops-agent-skills"
mkdir -p .claude/skills
cp -R "$SOURCE_REPO"/skills/cli-regex .claude/skills/
~~~

Start Claude Code in the project and invoke the skill:

~~~text
/cli-regex Parse the supplied IOS-XE output and generate a tested parser.
~~~

You can also ask naturally and let the description trigger it:

~~~text
Parse this operational CLI output into typed Python records. Use the
appropriate skill from this catalog, validate the parser with positive and negative
fixtures, and do not invent fields absent from the input.
~~~

See the [Claude Code skills documentation](https://code.claude.com/docs/en/skills).

### GitHub Copilot

Copilot supports project skills in .github/skills, .claude/skills, or
.agents/skills, depending on the Copilot surface and repository setup. It also
supports personal skills in ~/.copilot/skills or ~/.agents/skills.

For a repository-local Copilot installation:

~~~bash
SOURCE_REPO="/path/to/netdevops-agent-skills"
mkdir -p .github/skills
cp -R "$SOURCE_REPO"/skills/ntc-textfsm .github/skills/
~~~

In Copilot CLI, reload and inspect the skill:

~~~text
/skills reload
/skills list
/skills info ntc-textfsm
~~~

Invoke it when deterministic selection is important:

~~~text
Use the /ntc-textfsm skill to create a TextFSM template for the attached
show interface output, including tests for a missing interface and a changed
header.
~~~

See [Adding agent skills for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).

### Cursor

Cursor uses project rules in .cursor/rules and can reference project files with
the @ context mechanism. Cursor does not require converting this repository's
SKILL.md files into .mdc rules. Keep the source skills unchanged and reference
the selected skill explicitly.

Open the NetDevOps Agent Skills repository or copy the selected skill into the project,
then include it with @skills/<skill-slug>/SKILL.md. For a repeatable project
bridge, create .cursor/rules/netdevops-agent-skills.mdc:

~~~md
---
description: Use NetDevOps Agent Skills for network and infrastructure automation tasks.
globs:
alwaysApply: false
---

When a task matches a skill under skills/<skill-slug>/, read that skill's
SKILL.md before generating code. Follow its guardrails and run its documented
validation commands. Ask for explicit approval before live device, controller,
cloud, or destructive state changes.
~~~

Then use a prompt such as:

~~~text
@skills/ansible-pre-post-checks/SKILL.md
Use this skill to design a dry-run-safe pre-check, change, post-check, and
rollback workflow for the supplied Ansible playbook.
~~~

See [Cursor Rules](https://docs.cursor.com/context/rules-for-ai).

### Continue

Continue supports workspace rules in .continue/rules. Keep each NetDevOps Agent Skills
skill as the source of truth and add a small local rule that tells Continue
when to read the relevant SKILL.md. Do not merge the entire catalog into one
always-loaded rule; that wastes context and increases instruction conflicts.

Example .continue/rules/netdevops.md:

~~~md
# NetDevOps Agent Skills

For network automation, infrastructure-as-code, telemetry, or compliance
tasks, identify the matching directory under skills/, read its SKILL.md, and
follow its workflow, guardrails, examples, and validation commands. Load only
the skill or small combination of skills relevant to the request.
~~~

Then reference the selected file in the task or attach it through Continue's
file/context controls. See [Continue rules](https://docs.continue.dev/customize/rules).

### Other agents and local LLMs

If the host does not implement automatic skill discovery, use this fallback:

~~~text
Read skills/config-scrubber/SKILL.md before answering. Treat it as the
authoritative instructions for this task. Follow its guardrails, generate the
requested implementation, and run the validation commands it specifies.
~~~

If the agent has no filesystem access, paste one selected SKILL.md into the
conversation or configure the host's local knowledge/context directory. Load
one skill at a time; do not paste the entire catalog unless evaluating the
repository itself.

## How to ask an agent to use a skill

Give the agent the task inputs and state the skill explicitly when the work is
high-risk or automatic discovery is uncertain. A strong request includes:

1. The skill name or path.
2. The target platform, software version, and current toolchain.
3. Sanitized input artifacts: inventory, CLI output, API fixtures, YANG models,
   Terraform state, or existing code.
4. The desired output and whether the agent may edit files.
5. The required validation mode: parser tests, --check, plan, dry run,
   Batfish, Containerlab, or a lab device.
6. A clear statement that live changes require approval.

Example:

~~~text
Use skills/ntc-textfsm/SKILL.md.

Input: the sanitized IOS-XE show ip interface brief output in
fixtures/show_ip_interface_brief.txt.

Create a TextFSM template and pytest coverage for normal output, an empty
interface list, and an unexpected header. Keep the parser compatible with
TextFSM 2.x, do not use live device access, and run the documented validation
commands before reporting completion.
~~~

For multiple skills, state the order and boundary between them:

~~~text
Use ipam-subnetting to validate the address plan, then jinja2-config-base to
render the configuration. Keep IPAM data separate from the template, show the
rendered diff, and do not deploy anything.
~~~

## Offline and security model

These skills are written so an agent can reason from local files when internet
access is unavailable. Internet links in a skill are optional references, not
runtime requirements. Offline execution still requires the relevant local
packages, schemas, sanitized fixtures, provider plugins, container images,
licensed artifacts, or controller mocks.

Use [references/open-source-local.md](references/open-source-local.md) for
offline layouts, dependency pinning, fixtures, and quality gates.

Before using a skill with production data:

- Remove secrets, tokens, private keys, passwords, and customer identifiers.
- Use config-scrubber for network configuration and operational output.
- Review every bundled script before granting shell execution.
- Do not pre-approve shell, cloud, controller, or device tools unless the
  script and requested scope have been reviewed.
- Require a diff, dry run, plan, or lab proof before mutation.
- Treat vendor syntax as unverified until tested against the target platform,
  simulator, digital twin, or lab device.

Skills do not prove vendor interoperability merely because an LLM generated
syntactically plausible output. Live deployment remains the user's
responsibility and must use the organization's change-control process.

## Skill catalog

| Tier | Skill | Primary outcome |
|---|---|---|
| Basic | ipam-subnetting | Verified IPv4/IPv6 VLSM and IPAM seed data |
| Advanced | network-protocols-as-code | Vendor-neutral protocol models and device configuration |
| Basic | cli-regex | Named-group parsers for CLI and syslog output |
| Intermediate | ntc-textfsm | Tested TextFSM templates for network automation |
| Advanced | ttp-parsers | Hierarchical TTP parsers for structured output |
| Expert | pyats-genie | pyATS/Genie parsers and differential tests |
| Basic | netmiko-core | Safe SSH command and configuration execution |
| Intermediate | paramiko-ssh | Secure raw SSH transport and controlled command execution |
| Basic | config-diff-audit | Noise-filtered backups and reviewable diffs |
| Intermediate | scrapli-netmiko-threaded | Exception-isolated threaded fleet automation |
| Intermediate | network-rest-clients | Retry-safe clients for controller APIs |
| Advanced | nornir-napalm | Inventory-driven multi-vendor automation |
| Advanced | netops-data-pipelines | Validated network datasets and compliance reports |
| Expert | async-netops | Rate-limited asynchronous fleet automation |
| Expert | netops-cli-packaging | Installable Typer/Click automation CLIs |
| Basic | jinja2-config-base | Strict YAML data and Jinja configuration rendering |
| Intermediate | jinja2-multivendor-sot | Multi-vendor templates from one source of truth |
| Advanced | jinja2-custom-filters | Typed and tested Jinja filters and macros |
| Basic | pyang-xpath | YANG trees, XPath, XML, and JSON skeletons |
| Intermediate | netconf-restconf-payloads | Namespace-correct model-driven payloads |
| Advanced | ncclient-restconf | Validated NETCONF/RESTCONF Python clients |
| Advanced | netconf-automation | Capability-gated transactional NETCONF workflows |
| Expert | yang-model-dev | RFC 7950 YANG 1.1 models and linting |
| Basic | nso-device-onboarding | Repeatable Cisco NSO onboarding and sync |
| Intermediate | nso-xml-templates | Idempotent multi-NED NSO service templates |
| Advanced | nso-python-fastmap | Transaction-pure NSO FASTMAP services |
| Expert | nso-nano-services | Multi-stage NSO Nano Services and rollback design |
| Basic | ansible-netcli-playbooks | FQCN-compliant facts, commands, and backups |
| Basic | ansible-vault-hygiene | Vault-backed secret handling and leak prevention |
| Intermediate | ansible-resource-modules | Idempotent network resource modules |
| Intermediate | ansible-role-scaffolding | Multi-vendor roles with Molecule and linting |
| Intermediate | ansible-dynamic-inventory | Cached NetBox, cloud, and Terraform inventories |
| Intermediate | ansible-linux-networking | Linux routing, VLAN, FRR, nftables, and WireGuard |
| Advanced | ansible-pre-post-checks | Snapshot, change, assertion, and rollback workflows |
| Advanced | ansible-terraform-role | Plan-reviewed Terraform and Ansible handoff |
| Advanced | ansible-execution-envs | Pinned AAP/AWX execution environments |
| Expert | ansible-custom-plugins | Tested Ansible modules, filters, and connections |
| Basic | tf-vpc-foundations | VPC/VNet, routing, security, and state modules |
| Intermediate | tf-aws-networking | AWS multi-AZ, TGW, Direct Connect, and DNS |
| Intermediate | tf-azure-gcp-networking | Azure and GCP hub, routing, NAT, and DNS |
| Intermediate | tf-ansible-inventory | Terraform/OpenTofu to Ansible inventory handoff |
| Advanced | tf-firewall-policies | Stable-key, YAML-driven firewall policies |
| Advanced | tf-aci-sdwan-meraki | Controller-based network automation |
| Advanced | tf-module-hardening | Provider pinning, scans, and Terraform tests |
| Expert | tf-state-surgery | Safe state moves, imports, and removals |
| Basic | containerlab-topologies | Digital-twin topologies and test inventories |
| Basic | config-scrubber | Deterministic secret removal with structure preserved |
| Intermediate | netbox-nautobot-api | Idempotent source-of-truth API automation |
| Intermediate | gnmi-snmp-telemetry | gNMI, SNMP exporter, PromQL, and Grafana assets |
| Advanced | pysnmp-automation | Python PySNMP polling, walks, SET, traps, and informs |
| Advanced | acl-cis-compliance | CIS audits and ACL remediation analysis |
| Advanced | nac-cicd-pipelines | Lint, twin-test, plan, approval, and deploy pipelines |
| Expert | batfish-validation | Offline routing, ACL, BGP, and reachability proofs |

## Validate the catalog

The repository validator is dependency-free and checks frontmatter, required
sections, descriptions, naming, line limits, and catalog completeness:

~~~bash
python3 scripts/validate_skills.py
~~~

Expected result:

~~~text
Validated N skills: N valid, 0 invalid.
~~~

Each skill also documents its own validation commands. Run those commands when
working with that skill; the repository validator does not replace pytest,
ansible-lint, pyang, terraform validate, tofu validate, Batfish, Containerlab,
or vendor/controller tests.

## Contributing a skill

1. Add or update skills/<lowercase-hyphenated-slug>/SKILL.md.
2. Keep the skill self-contained and put supporting scripts under that skill's directory.
3. Include explicit trigger conditions, input validation, guardrails, examples, failure modes, and offline validation steps.
4. Do not include credentials, private keys, customer configurations, raw production backups, proprietary device images, or restricted vendor files.
5. Run python3 scripts/validate_skills.py before opening a pull request.

## Documentation references

- [Agent Skills open standard](https://agentskills.io/)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [GitHub Copilot agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [Cursor Rules](https://docs.cursor.com/context/rules-for-ai)
- [Continue Rules](https://docs.continue.dev/customize/rules)

## License

MIT. Vendor names and product marks remain the property of their respective
owners.
