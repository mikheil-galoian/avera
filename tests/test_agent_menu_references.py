"""Agent-OS consistency guard.

The agent operating system (``AGENTS.md`` + ``00_AGENT_MENU/``) drives how an
agent navigates the repository. It previously drifted from the codebase: a
missing root ``ARCHITECTURE.md``, ``ROUTER.md`` pointing at zone guides that did
not exist, and stale module names in ``PROJECT_MAP.md``.

These tests fail when that drift returns — i.e. when a *required* document or a
routing-table task template referenced by the agent menu no longer exists on
disk. Intentionally-not-yet-created zone guides (Supabase / Deployment /
Integrations / Database) are explicitly allowed to be absent and are asserted to
be marked as optional rather than mandatory.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MENU = REPO_ROOT / "00_AGENT_MENU"

# Documents the ROUTER's mandatory reading order and core menu depend on.
# If any of these goes missing, an agent following the rules hits a dead end.
REQUIRED_DOCS = [
    "AGENTS.md",
    "ARCHITECTURE.md",
    "00_AGENT_MENU/ROUTER.md",
    "00_AGENT_MENU/PROJECT_MAP.md",
    "00_AGENT_MENU/TASK_TYPES.md",
    "00_AGENT_MENU/ACTIVE_TASK.md",
    "00_AGENT_MENU/SAFETY_RULES.md",
]

# Zone guides ROUTER references but that are intentionally not created yet
# (the project has no Supabase / external DB). These are allowed to be absent.
OPTIONAL_ZONE_GUIDES = {
    "SUPABASE.md",
    "DEPLOYMENT.md",
    "INTEGRATIONS.md",
    "DATABASE.md",
}


@pytest.mark.parametrize("relpath", REQUIRED_DOCS)
def test_required_agent_docs_exist(relpath: str) -> None:
    """Every document the agent menu mandates must exist."""
    path = REPO_ROOT / relpath
    assert path.is_file(), (
        f"Agent-menu requires {relpath!r} but it is missing. "
        f"Either restore the file or update 00_AGENT_MENU/ROUTER.md."
    )


def test_router_task_templates_exist() -> None:
    """Every task template named in ROUTER's routing table must exist on disk."""
    router = (MENU / "ROUTER.md").read_text(encoding="utf-8")
    # Matches references like `templates/bugfix.task.md`.
    referenced = sorted(set(re.findall(r"templates/[\w./-]+\.task\.md", router)))
    assert referenced, "ROUTER.md should reference at least one task template."
    missing = [rel for rel in referenced if not (MENU / rel).is_file()]
    assert not missing, (
        f"ROUTER.md references task templates that do not exist: {missing}. "
        f"Add them under 00_AGENT_MENU/templates/ or fix the routing table."
    )


def test_optional_zone_guides_are_not_mandatory() -> None:
    """Absent zone guides must be presented as optional, never as a hard step.

    Guards against silently promoting a non-existent guide into the mandatory
    reading order. If such a guide is later created, this test still passes.
    """
    router = (MENU / "ROUTER.md").read_text(encoding="utf-8")
    # The "Обязательный порядок" (mandatory order) section is the numbered list
    # at the top, before the first level-2 heading after it. We simply require
    # that any absent zone guide is not listed in that mandatory block.
    mandatory_block = router.split("## Routing Rules")[0]
    for guide in OPTIONAL_ZONE_GUIDES:
        exists = (MENU / guide).is_file()
        if not exists:
            assert guide not in mandatory_block, (
                f"{guide} does not exist yet but appears in the mandatory "
                f"reading order of ROUTER.md. Mark it optional or create it."
            )
