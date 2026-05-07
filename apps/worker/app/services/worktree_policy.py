"""Worktree boundary policy for WRK-03.

Ensures all task worktrees stay under the configured .worktrees root.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4


class WorktreePolicyError(Exception):
    """Raised when requested worktree path violates boundary policy."""


def _default_worktree_root() -> Path:
    """Platform-safe default: repo-local .worktrees directory."""
    # Walk up from this file to find the project root (contains .git or apps/)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists() or (parent / "apps").exists():
            return parent / ".worktrees"
    # Fallback: current working directory
    return Path.cwd() / ".worktrees"


def _resolve_worktree_root() -> Path:
    """Resolve worktree root from env or platform-safe default."""
    env_root = os.environ.get("WORKTREE_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return _default_worktree_root().resolve()


WORKTREE_ROOT = _resolve_worktree_root()


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
