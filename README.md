# netdevops-agent-skills

Production-oriented Agent Skills for network automation, infrastructure as
code, data-center fabrics, cloud networking, observability, compliance, and
SRE workflows.

Each skill is a self-contained directory with a SKILL.md file. It gives an AI
coding agent the domain context, implementation workflow, guardrails, examples,
and validation commands needed for a specific task.

## Quick start

Clone the repository:

~~~bash
git clone https://github.com/vsachin094/netdevops-agent-skills.git
cd netdevops-agent-skills
~~~

Inspect a skill:

~~~bash
sed -n '1,240p' skills/ntc-textfsm/SKILL.md
~~~

The skills do not install Python packages, credentials, device access, cloud
permissions, controllers, or vendor licenses. Install only the dependencies
listed in the selected skill's compatibility metadata.

## Install skills

Install all skills into a project-local Agent Skills directory:

~~~bash
mkdir -p .agents/skills
cp -R /path/to/netdevops-agent-skills/skills/* .agents/skills/
~~~

Or install only the skills needed by the project:

~~~bash
mkdir -p .agents/skills
cp -R /path/to/netdevops-agent-skills/skills/paramiko-ssh .agents/skills/
cp -R /path/to/netdevops-agent-skills/skills/netconf-automation .agents/skills/
cp -R /path/to/netdevops-agent-skills/skills/pysnmp-automation .agents/skills/
~~~

Keep each skill directory intact:

~~~text
.agents/skills/<skill-slug>/SKILL.md
~~~

Do not flatten the files. Skill-local helper scripts use relative paths.

## Agent integration

Use the native project location when the host supports Agent Skills:

| Agent | Project location | Explicit use |
|---|---|---|
| Claude Code | .claude/skills/<skill-slug>/SKILL.md | /skill-slug |
| GitHub Copilot | .github/skills or .agents/skills | /skill-slug or natural language |
| Cursor | Keep skills in the workspace and reference the file with @ | @skills/<skill-slug>/SKILL.md |
| Continue | Keep skills in the workspace and reference the file from .continue/rules | Project rule or attached file |
| Other/local LLM | Any readable local directory | Tell the agent to read the selected SKILL.md |

Example request:

~~~text
Use skills/netconf-automation/SKILL.md.

Build a Python ncclient workflow for the supplied device capabilities and YANG
payload. Validate namespaces, check candidate support, use confirmed commit
where available, and run the documented tests. Do not connect to production.
~~~

If the agent cannot discover skills automatically, explicitly provide the
selected SKILL.md as file context or paste it into the conversation. Load only
the skills relevant to the task.

## Skill areas

Browse the skills directory to select the appropriate workflow:

- Python transport: Paramiko SSH, NETCONF, PySNMP, Netmiko, Scrapli
- Parsing: regex, TextFSM, TTP, pyATS/Genie
- Templates and models: Jinja2, YANG, XPath, NETCONF, RESTCONF
- Ansible: playbooks, roles, inventories, resource modules, execution environments
- Terraform/OpenTofu: VPCs, cloud networking, firewalls, state, controllers
- Validation: Batfish, Containerlab, ACL/CIS compliance, pre/post checks
- Data and telemetry: NetBox, Nautobot, gNMI, SNMP exporters, PromQL, Grafana

## Offline and safety guidance

The skills are written to remain useful without internet access. Offline use
still requires the relevant local packages, YANG modules, provider plugins,
sanitized fixtures, container images, simulators, or controller mocks.

Before giving an agent access to production data or tools:

- Remove passwords, tokens, private keys, and customer identifiers.
- Review bundled scripts before allowing shell execution.
- Use config-scrubber for network configuration and operational output.
- Require a diff, dry run, plan, or lab test before mutation.
- Treat vendor syntax as unverified until tested against the target platform.
- Never claim live device or controller validation without live access.

See [references/open-source-local.md](references/open-source-local.md) for
offline dependency and fixture guidance.

## Validate the repository

The dependency-free validator checks every skill's frontmatter, required
sections, naming, descriptions, and file limits:

~~~bash
python3 scripts/validate_skills.py
~~~

Each skill also documents its own tool-specific checks, such as pytest,
ansible-lint, pyang, terraform validate, Batfish, or Containerlab.

## Contributing

Add a skill under skills/<lowercase-hyphenated-slug>/SKILL.md. Keep the skill
self-contained, document its dependencies and failure modes, include offline
validation steps, and place supporting scripts inside that skill directory.

Do not commit credentials, private keys, customer configurations, raw
production backups, proprietary images, or restricted vendor files.

Run the validator before opening a pull request:

~~~bash
python3 scripts/validate_skills.py
~~~

## Documentation

- [Agent Skills standard](https://agentskills.io/)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [GitHub Copilot agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [Cursor Rules](https://docs.cursor.com/context/rules-for-ai)
- [Continue Rules](https://docs.continue.dev/customize/rules)
- [Offline execution guide](references/open-source-local.md)

## License

MIT. Vendor names and product marks remain the property of their respective
owners.
