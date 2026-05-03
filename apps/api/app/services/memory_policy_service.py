"""Memory access policy — path validation, write tiers, secrets guard.

Enforces:
- Path traversal protection (no ../, no absolute paths, no drive letters)
- Write access tiers: free / approval_required / forbidden
- Secrets detection before writes
- Only .md files inside .ai_memory/
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from pathlib import Path, PurePosixPath

from app.config import settings
from app.schemas.memory import contains_forbidden_content

logger = logging.getLogger(__name__)


class AccessTier(str, Enum):
    """Write access level for a memory path."""

    FREE = "free"  # Any agent can write
    APPROVAL_REQUIRED = "approval_required"  # Needs human approval
    FORBIDDEN = "forbidden"  # Never writable via API


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

# Patterns that indicate path traversal or illegal paths
_TRAVERSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.\."),  # ..
    re.compile(r"^/"),  # absolute Unix
    re.compile(r"^[A-Za-z]:"),  # Windows drive letter
    re.compile(r"\\"),  # backslash (force forward-slash only)
]

# Only .md files are allowed
_ALLOWED_EXTENSION = ".md"


class PathValidationError(Exception):
    """Raised when a memory path fails validation."""

    pass


class SecretsDetectedError(Exception):
    """Raised when content contains forbidden secret patterns."""

    pass


class WriteForbiddenError(Exception):
    """Raised when write is attempted to a forbidden path."""

    pass


def validate_memory_path(relative_path: str, vault_path: Path | None = None) -> Path:
    """Validate and resolve a relative path inside the vault.

    Args:
        relative_path: Forward-slash relative path inside .ai_memory/.
        vault_path: Override vault root (for testing).

    Returns:
        Resolved absolute Path inside the vault.

    Raises:
        PathValidationError: If path is invalid or escapes vault.
    """
    vault = Path(vault_path or settings.MEMORY_VAULT_PATH).resolve()

    # Check traversal patterns
    for pattern in _TRAVERSAL_PATTERNS:
        if pattern.search(relative_path):
            raise PathValidationError(
                f"Invalid path: '{relative_path}' contains forbidden pattern"
            )

    # Must end with .md
    if not relative_path.lower().endswith(_ALLOWED_EXTENSION):
        raise PathValidationError(
            f"Only {_ALLOWED_EXTENSION} files are allowed, got: '{relative_path}'"
        )

    # Must not be empty
    clean = relative_path.strip("/")
    if not clean:
        raise PathValidationError("Path cannot be empty")

    # Resolve and verify it stays inside vault
    resolved = (vault / clean).resolve()

    # Verify the resolved path is inside vault
    try:
        resolved.relative_to(vault)
    except ValueError:
        raise PathValidationError(
            f"Path escapes vault: '{relative_path}'"
        )

    # Verify no symlink escape (resolve the parent if it exists)
    if resolved.parent.exists():
        real_parent = resolved.parent.resolve()
        try:
            real_parent.relative_to(vault)
        except ValueError:
            raise PathValidationError(
                f"Symlink escape detected for path: '{relative_path}'"
            )

    return resolved


def get_write_tier(relative_path: str) -> AccessTier:
    """Determine the write access tier for a relative path inside the vault.

    Rules:
    - .obsidian/ → FORBIDDEN
    - templates/ → FORBIDDEN (managed by provisioning)
    - README.md at root level → APPROVAL_REQUIRED
    - _INDEX.md → APPROVAL_REQUIRED
    - current_state.md (root) → APPROVAL_REQUIRED
    - decisions/* → APPROVAL_REQUIRED
    - projects/*/overview.md → APPROVAL_REQUIRED
    - projects/*/architecture.md → APPROVAL_REQUIRED
    - projects/*/decisions.md → APPROVAL_REQUIRED
    - projects/*/current_state.md → FREE
    - projects/*/agent_notes.md → FREE
    - projects/*/tasks.md → FREE
    - projects/*/known_issues.md → FREE
    - tasks/* → FREE
    - agents/* → APPROVAL_REQUIRED
    - everything else → APPROVAL_REQUIRED
    """
    clean = relative_path.strip("/")
    parts = PurePosixPath(clean).parts

    # .obsidian → FORBIDDEN
    if parts[0] == ".obsidian":
        return AccessTier.FORBIDDEN

    # templates → FORBIDDEN (managed by provisioning only)
    if parts[0] == "templates":
        return AccessTier.FORBIDDEN

    # tasks/* → FREE (task summaries)
    if parts[0] == "tasks" and len(parts) == 2:
        return AccessTier.FREE

    # projects/<slug>/<file>
    if parts[0] == "projects" and len(parts) == 3:
        filename = parts[2]
        free_files = {
            "current_state.md",
            "agent_notes.md",
            "tasks.md",
            "known_issues.md",
        }
        if filename in free_files:
            return AccessTier.FREE
        # overview, architecture, decisions → approval
        return AccessTier.APPROVAL_REQUIRED

    # Root-level files
    if len(parts) == 1:
        if parts[0] == "current_state.md":
            return AccessTier.APPROVAL_REQUIRED
        if parts[0] == "_INDEX.md":
            return AccessTier.APPROVAL_REQUIRED
        if parts[0] == "README.md":
            return AccessTier.APPROVAL_REQUIRED
        return AccessTier.APPROVAL_REQUIRED

    # agents/* → APPROVAL_REQUIRED
    if parts[0] == "agents":
        return AccessTier.APPROVAL_REQUIRED

    # decisions/* → APPROVAL_REQUIRED
    if parts[0] == "decisions":
        return AccessTier.APPROVAL_REQUIRED

    # Default: approval required
    return AccessTier.APPROVAL_REQUIRED


def check_write_allowed(
    relative_path: str,
    content: str,
    *,
    bypass_approval: bool = False,
) -> AccessTier:
    """Full write permission check.

    Args:
        relative_path: Forward-slash path inside vault.
        content: Text content to write.
        bypass_approval: If True, treat APPROVAL_REQUIRED as allowed
                         (for internal system use).

    Returns:
        The access tier (caller can decide what to do).

    Raises:
        PathValidationError: If path is invalid.
        SecretsDetectedError: If content contains secrets.
        WriteForbiddenError: If path is forbidden.
    """
    # 1. Validate path
    validate_memory_path(relative_path)

    # 2. Check secrets
    if contains_forbidden_content(content):
        raise SecretsDetectedError(
            "Content contains forbidden patterns (secrets/tokens/passwords)"
        )

    # 3. Check write tier
    tier = get_write_tier(relative_path)

    if tier == AccessTier.FORBIDDEN:
        raise WriteForbiddenError(
            f"Writing to '{relative_path}' is forbidden"
        )

    if tier == AccessTier.APPROVAL_REQUIRED and not bypass_approval:
        raise WriteForbiddenError(
            f"Writing to '{relative_path}' requires approval. "
            f"Use bypass_approval=True for system-level operations."
        )

    return tier
