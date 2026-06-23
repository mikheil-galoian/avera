# Contributing to AVERA

Thank you for your interest in contributing to AVERA — an engineering change verification evidence platform for safety-critical systems.

## Before You Start

AVERA is used in safety-critical contexts (ISO 26262, DO-178C, EN 50128, IEC 62304). Contributions must maintain deterministic, auditable behavior. Any change that affects evidence generation, artifact comparison, or release decisions requires careful review.

## Ways to Contribute

- **Bug reports** — Use the bug report issue template. Include the exact artifact input, expected output, and actual output.
- **Feature requests** — Use the feature request template. Describe the compliance standard or domain context that motivates the request.
- **Documentation** — Improvements to README, examples, and fixture documentation are always welcome.
- **New adapters** — Adding support for new artifact formats (e.g., new tool exports). See `src/avera/adapters/` for existing patterns.
- **New domains** — Extending AVERA to new safety-critical domains (railway, medical, nuclear). Open an issue first to discuss scope.

## Development Setup

```bash
git clone https://github.com/YOUR_ORG/avera.git
cd avera
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Core Principles

1. **Determinism** — Given the same inputs, AVERA must always produce the same output. No randomness, no time-dependent behavior in core logic.
2. **Auditability** — Every decision must be traceable to specific artifact evidence. No opaque scoring.
3. **Conservative defaults** — When evidence is ambiguous or missing, AVERA should lean toward flagging rather than approving.
4. **No external dependencies in core** — The core pipeline must run fully offline. Network calls are only permitted in optional integrations.

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Add or update tests. All new adapters must have fixture-based tests.
3. Run the full test suite: `pytest tests/ -v`
4. Ensure no existing tests are broken.
5. Open a PR using the pull request template.
6. One maintainer approval is required before merge.

## Commit Style

Use conventional commits:
- `feat:` — new feature or adapter
- `fix:` — bug fix
- `test:` — test additions or fixes
- `docs:` — documentation only
- `chore:` — tooling, CI, dependencies

## Questions

Open a GitHub Discussion or file an issue with the `question` label.
