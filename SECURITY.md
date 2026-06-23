# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (main) | ✅ Active |
| older releases | ❌ Not supported |

## Scope

AVERA processes engineering artifacts (verification logs, test reports, requirement exports) in safety-critical contexts. Security considerations include:

- **Artifact integrity** — AVERA must not silently modify or corrupt input artifacts during processing.
- **Evidence tampering** — No mechanism should allow altering audit evidence post-generation.
- **Dependency vulnerabilities** — Third-party library vulnerabilities that could affect artifact parsing or output correctness.
- **Injection via artifact content** — Malformed or adversarially crafted artifacts must not cause unsafe behavior in the pipeline.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing: **mgaloyan79@gmail.com**

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Affected component (adapter, core, API, CLI)
- Potential impact in a safety-critical deployment context
- Any suggested fix (optional)

We will acknowledge receipt within **72 hours** and provide an initial assessment within **7 days**.

## Response Process

1. Confirm the vulnerability and assess severity
2. Develop a fix on a private branch
3. Release a patch version
4. Publish a security advisory on GitHub
5. Credit the reporter (unless they prefer anonymity)

## Out of Scope

- Vulnerabilities in user infrastructure (CI runners, artifact storage)
- Issues requiring physical access to the machine running AVERA
- Social engineering attacks
