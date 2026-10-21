---
name: config-sanitizer
description: "Sanitize network configurations and logs before sharing with agents, vendors, or tickets by replacing secrets and sensitive addresses with deterministic placeholders while preserving topology relationships. Use this skill whenever raw enterprise configuration leaves its controlled system."
license: MIT
compatibility: Python 3.10+ standard library; optional vendor-specific secret patterns; input supplied by the user
---

# Configuration Sanitizer (Basic)

Anonymization must preserve enough structure for debugging without preserving credentials or identifiable production data. Scrubbing is not encryption and must be reviewed before external sharing.

## Core Engineering Capabilities

- Replace passwords, Type 5/7/8/9 hashes, SNMP communities, BGP/IKE/TACACS keys, private keys, tokens, and sensitive hostnames.
- Map public/private addresses to RFC documentation ranges consistently so subnet relationships, duplicate detection, and topology remain useful.
- Produce a scrub report listing pattern classes and replacement counts.

## Strict Engineering Guardrails (Anti-Hallucination & Best Practices)

- Use deterministic placeholders and a mapping held only in the controlled operator context; never put the reversible map beside the output.
- Fail on private-key blocks, unknown secret-like fields, or binary content rather than claiming a clean result.
- Preserve line structure, vendor syntax, comments, and relationships where possible, but prefer removing a value over leaking it.
- Do not treat Type 7 or hashed values as safe; they are still sensitive.
- Review the scrubbed artifact manually and scan it again before sharing.

## Step-by-Step Agent Execution Workflow

### Phase 1 (Intake & Scope)

Determine the input syntax, vendor, secret classes, identifier-preservation requirement, and whether the output must remain parseable. Treat unknown credential-like values as findings rather than guessing their meaning.

### Phase 2 (Implementation)

Build deterministic redaction rules with stable placeholders, preserving line structure, indentation, references, and topology identifiers. Keep reversible mappings outside the repository and never emit original secrets to logs.

### Phase 3 (Verification)

Run the helper against known tokens, keys, hashes, URLs, certificates, and near-miss values. Parse the scrubbed output where possible and verify repeated runs produce identical output.

1. Identify output destination and required topology fidelity.
2. Apply ordered secret/address patterns and collect replacement counts.
3. Scan residual output, review suspicious lines, and publish only the scrubbed artifact plus a non-sensitive report.

## Production Code / Template Example

### Input / Requirement

Provide sanitized or synthetic configuration samples, the secret patterns to remove, identifiers that must remain stable, and the downstream parser or sharing requirement.

### Output / Generated Code

Return scrubbed output, a findings summary, the rule set, and positive/negative fixtures. State any value that remains ambiguous and needs operator review.

```text
snmp-server community SuperSecret RO
 -> snmp-server community <SNMP_COMMUNITY_001> RO

interface 10.20.30.1/24
 -> interface 198.51.100.1/24
```

```python
import re
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class ScrubResult:
    text: str
    replacements: Dict[str, int] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)

SECRET_PATTERNS = [
    (re.compile(r'(password|secret|key)\s+(\S+)', re.I), '<SECRET_{n}>'),
    (re.compile(r'(community)\s+(\S+)', re.I), '<SNMP_COMMUNITY_{n}>'),
    (re.compile(r'(bgp|ike|tacacs).*\s(key|secret)\s+(\S+)', re.I), '<{1}_{n}>'),
    (re.compile(r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----.*?-----END \1 PRIVATE KEY-----', re.DOTALL), '<PRIVATE_KEY_{n}>'),
]

IPV4_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b')
IPV6_PATTERN = re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b')

def scrub_config(text: str) -> ScrubResult:
    result = ScrubResult(text=text)
    counters = {}
    
    for pattern, placeholder in SECRET_PATTERNS:
        def repl(m):
            key = placeholder.format(n=counters.get(placeholder, 0) + 1)
            counters[placeholder] = counters.get(placeholder, 0) + 1
            result.replacements[key] = result.replacements.get(key, 0) + 1
            return m.group(0).replace(m.group(2), key) if len(m.groups()) > 1 else key
        result.text = pattern.sub(repl, result.text)
    
    # Address pseudonymization (simplified)
    ipv4_map = {}
    def ipv4_repl(m):
        ip = m.group(0)
        if ip not in ipv4_map:
            # Map to RFC 5737 documentation range
            ipv4_map[ip] = f"198.51.100.{len(ipv4_map) + 1}"
        return ipv4_map[ip]
    result.text = IPV4_PATTERN.sub(ipv4_repl, result.text)
    
    # Check for remaining suspicious content
    if re.search(r'-----BEGIN.*PRIVATE KEY-----', result.text):
        result.findings.append("Possible unscrubbed private key block")
    
    return result
```

## Validation, Linting & Testing Commands

- Test every secret class, multiline key, repeated value, address mapping, false positive, and encoding edge case.
- Search output for known secret markers and private-key boundaries.
- Run `python3 scripts/validate_skills.py`.

## References

- [RFC 5737 documentation IPv4 ranges](https://www.rfc-editor.org/rfc/rfc5737.html)
- [RFC 3849 documentation IPv6 prefix](https://www.rfc-editor.org/rfc/rfc3849.html)

## Offline Execution Contract

Scrubbing must be fully local and deterministic. If a vendor-specific secret pattern is unknown, preserve the line for operator review and fail closed rather than claiming the output is safe to share.

## Architecture & Technical Design Patterns

Apply redaction in ordered passes: private-key blocks and certificates first; credential-bearing directives second; hashes/tokens/communities third; then address and hostname pseudonymization. Use a deterministic mapping keyed by the original value during one run so repeated occurrences remain related, but do not persist the reversible map with the output. Preserve address-family and prefix relationships by mapping within a documentation range, not by replacing each octet independently.

Scan the result for private-key boundaries, password/secret/community/token markers, known production prefixes, and original sensitive hostnames. Produce replacement counts and suspicious residual lines. Treat scrubbed output as still sensitive until a human reviews it; scrubbing is not encryption and cannot guarantee removal of secrets hidden in comments, binary blobs, or vendor-specific obfuscation.