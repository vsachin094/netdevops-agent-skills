#!/usr/bin/env python3
"""Validate NetDevOps Agent Skills against the repository contract."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

REQUIRED_SECTIONS = (
    "## Core Engineering Capabilities",
    "## Architecture & Technical Design Patterns",
    "## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)",
    "## Step-by-Step Agent Execution Workflow",
    "## Production Code / Template Example",
    "## Validation, Linting & Testing Commands",
)
ALLOWED_KEYS = {"name", "description", "license", "compatibility"}
TIERS = {"Basic", "Intermediate", "Advanced", "Expert"}
MARKDOWN_LINK = re.compile(r"(?<!)\[[^\]]*\]\(([^)]+)\)")


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["frontmatter must start at line 1 with ---"]
    end = text.find("\n---", 4)
    if end == -1:
        return {}, ["frontmatter closing --- is missing"]
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or ":" not in line:
            errors.append(f"invalid frontmatter line: {line!r}")
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key not in ALLOWED_KEYS:
            errors.append(f"unsupported frontmatter key: {key}")
        values[key] = value.strip('"\'')
    return values, errors


def validate_local_links(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(text):
        target = target.strip().split(maxsplit=1)[0].strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        destination = (path.parent / unquote(parsed.path)).resolve()
        if not destination.exists():
            errors.append(f"broken local link: {target}")
    return errors


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    slug = path.parent.name
    metadata, errors = parse_frontmatter(text)
    errors.extend(validate_local_links(path))
    if metadata.get("name") != slug:
        errors.append(f"name must exactly match directory slug {slug!r}")
    description = metadata.get("description", "")
    if not description:
        errors.append("description is required")
    if len(description) > 1024:
        errors.append("description exceeds 1024 characters")
    # Tier is in title, not description - keep description clean
    if "Use this skill when" not in description:
        errors.append("description must state when to trigger the skill")
    if metadata.get("license") != "MIT":
        errors.append("license must be MIT")
    if not metadata.get("compatibility"):
        errors.append("compatibility is required")
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing section: {section}")
    # Accept both old and new workflow phase names
    old_phases = (
        "### Phase 1 (Ingestion & Validation)",
        "### Phase 2 (Generation)",
        "### Phase 3 (Self-Verification)",
    )
    new_phases = (
        "### Phase 1 (Intake & Scope)",
        "### Phase 2 (Implementation)",
        "### Phase 3 (Verification)",
    )
    headings = set(text.splitlines())
    for old, new in zip(old_phases, new_phases):
        if old not in headings and new not in headings:
            errors.append(f"missing workflow phase: {old} or {new}")
    for example_section in ("### Input / Requirement", "### Output / Generated Code"):
        if example_section not in text:
            errors.append(f"missing example subsection: {example_section}")
    if not re.search(r"^# .+\((Basic|Intermediate|Advanced|Expert)\)$", text, re.M):
        errors.append("missing tiered top-level title")
    return errors


def validate_readme(root: Path) -> list[str]:
    path = root / "README.md"
    errors = validate_local_links(path)
    text = path.read_text(encoding="utf-8")
    listed_skills = set(re.findall(r"^\| `([a-z0-9-]+)` \|", text, re.M))
    actual_skills = {skill.parent.name for skill in (root / "skills").glob("*/SKILL.md")}
    for slug in sorted(actual_skills - listed_skills):
        errors.append(f"skill missing from README category tables: {slug}")
    for slug in sorted(listed_skills - actual_skills):
        errors.append(f"README references unknown skill: {slug}")
    return errors


def main(root: Path) -> int:
    files = sorted((root / "skills").glob("*/SKILL.md"))
    if not files:
        print("No SKILL.md files found; scaffold validation is clean.")
        return 0
    failures = 0
    for path in files:
        errors = validate_file(path)
        if errors:
            failures += 1
            for error in errors:
                print(f"ERROR {path}: {error}")
        else:
            print(f"OK    {path}")
    readme_errors = validate_readme(root)
    if readme_errors:
        failures += 1
        for error in readme_errors:
            print(f"ERROR {root / 'README.md'}: {error}")
    else:
        print(f"OK    {root / 'README.md'}")
    print(f"Validated {len(files)} skills: {len(files) - failures} valid, {failures} invalid.")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    raise SystemExit(main(args.root.resolve()))