"""Memory CRUD service — read, write, append, list operations on .ai_memory vault.

All operations go through memory_policy_service for access control.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.schemas.memory import (
    MemoryFileListResult,
    MemoryFileRead,
    MemoryFileWrite,
)
from app.services.memory_policy_service import (
    AccessTier,
    PathValidationError,
    check_write_allowed,
    get_write_tier,
    validate_memory_path,
)

logger = logging.getLogger(__name__)


class MemoryFileNotFoundError(Exception):
    """Raised when a memory file is not found."""

    pass


class MemoryService:
    """Read, write, append, list operations on the .ai_memory vault."""

    def __init__(self, vault_path: str | None = None) -> None:
        self._vault_path = Path(vault_path or settings.MEMORY_VAULT_PATH).resolve()

    @property
    def vault_path(self) -> Path:
        return self._vault_path

    # ── Read ──────────────────────────────────────────────────────────

    def read_file(self, relative_path: str) -> MemoryFileRead:
        """Read a markdown file from the vault.

        Args:
            relative_path: Forward-slash path relative to vault root.

        Returns:
            MemoryFileRead with content and metadata.

        Raises:
            PathValidationError: If path is invalid.
            FileNotFoundError_: If file doesn't exist.
        """
        resolved = validate_memory_path(relative_path, vault_path=self._vault_path)

        if not resolved.is_file():
            raise MemoryFileNotFoundError(f"File not found: {relative_path}")

        content = resolved.read_text(encoding="utf-8")
        stat = resolved.stat()

        return MemoryFileRead(
            path=relative_path,
            content=content,
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )

    # ── Write (full replace) ──────────────────────────────────────────

    def write_file(
        self,
        relative_path: str,
        content: str,
        *,
        bypass_approval: bool = False,
    ) -> MemoryFileWrite:
        """Write (create or replace) a markdown file in the vault.

        Args:
            relative_path: Forward-slash path relative to vault root.
            content: Markdown content.
            bypass_approval: Allow writing to approval-required paths.

        Returns:
            MemoryFileWrite result.

        Raises:
            PathValidationError: Invalid path.
            SecretsDetectedError: Content contains secrets.
            WriteForbiddenError: Write not allowed for this path.
        """
        tier = check_write_allowed(
            relative_path, content, bypass_approval=bypass_approval
        )
        resolved = validate_memory_path(relative_path, vault_path=self._vault_path)

        # Ensure parent directory exists
        resolved.parent.mkdir(parents=True, exist_ok=True)

        resolved.write_text(content, encoding="utf-8")

        logger.info("memory_write: path=%s tier=%s", relative_path, tier)

        return MemoryFileWrite(
            path=relative_path,
            status="written",
            access_tier=tier,
        )

    # ── Append ────────────────────────────────────────────────────────

    def append_file(
        self,
        relative_path: str,
        content: str,
        *,
        bypass_approval: bool = False,
    ) -> MemoryFileWrite:
        """Append content to a markdown file in the vault.

        Creates the file if it doesn't exist.

        Args:
            relative_path: Forward-slash path relative to vault root.
            content: Content to append.
            bypass_approval: Allow appending to approval-required paths.

        Returns:
            MemoryFileWrite result.
        """
        # For append, we check both existing content + new content
        resolved = validate_memory_path(relative_path, vault_path=self._vault_path)

        existing_content = ""
        if resolved.is_file():
            existing_content = resolved.read_text(encoding="utf-8")

        combined = existing_content + content
        tier = check_write_allowed(
            relative_path, combined, bypass_approval=bypass_approval
        )

        resolved.parent.mkdir(parents=True, exist_ok=True)

        with open(resolved, "a", encoding="utf-8") as f:
            f.write(content)

        logger.info("memory_append: path=%s tier=%s", relative_path, tier)

        return MemoryFileWrite(
            path=relative_path,
            status="appended",
            access_tier=tier,
        )

    # ── List ──────────────────────────────────────────────────────────

    def list_files(
        self,
        prefix: str | None = None,
        project_slug: str | None = None,
    ) -> MemoryFileListResult:
        """List markdown files in the vault.

        Args:
            prefix: Optional path prefix to filter by.
            project_slug: Optional project slug (shorthand for projects/<slug>/).

        Returns:
            MemoryFileListResult with list of relative paths.
        """
        if project_slug:
            search_dir = self._vault_path / "projects" / project_slug
        elif prefix:
            # Validate prefix doesn't escape vault
            clean = prefix.strip("/")
            search_dir = self._vault_path / clean
            # Verify stays inside vault
            try:
                search_dir.resolve().relative_to(self._vault_path)
            except ValueError:
                raise PathValidationError(f"Prefix escapes vault: '{prefix}'")
        else:
            search_dir = self._vault_path

        files: list[str] = []
        if search_dir.is_dir():
            for f in sorted(search_dir.rglob("*.md")):
                if f.is_file():
                    # Skip .obsidian and .hidden
                    parts = f.relative_to(self._vault_path).parts
                    if any(p.startswith(".") for p in parts):
                        continue
                    rel = str(f.relative_to(self._vault_path)).replace("\\", "/")
                    files.append(rel)

        return MemoryFileListResult(
            files=files,
            total=len(files),
            prefix=prefix,
            project_slug=project_slug,
        )

    # ── Get access tier ───────────────────────────────────────────────

    def get_access_tier(self, relative_path: str) -> AccessTier:
        """Get the write access tier for a path (without writing).

        Args:
            relative_path: Forward-slash path inside vault.

        Returns:
            AccessTier enum value.
        """
        return get_write_tier(relative_path)
