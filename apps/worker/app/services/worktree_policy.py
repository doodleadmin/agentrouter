"""Worktree boundary policy for WRK-03.

Ensures all task worktrees stay under the configured .worktrees root.
"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4


class WorktreePolicyError(Exception):
    """Raised when requested worktree path violates boundary policy."""


WORKTREE_ROOT = Path(r"F:\dev\agentrouter\.worktrees")


def build_worktree_path(external_id: str) -> Path:
    """Build deterministic-safe worktree path under WORKTREE_ROOT."""
    safe_external = re.sub(r"[^a-zA-Z0-9_-]", "-", external_id).strip("-") or "task"
    short_uuid = str(uuid4())[:8]
    return WORKTREE_ROOT / f"task-{safe_external}-{short_uuid}"


def validate_worktree_path(path: Path, *, root: Path = WORKTREE_ROOT) -> Path:
    """Validate worktree path remains inside worktree root.

    Uses resolve()+relative_to() boundary check.
    """
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise WorktreePolicyError(
            f"Worktree path escapes root: {resolved_path}"
        ) from exc
    return resolved_path
