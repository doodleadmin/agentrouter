"""Tests for memory_policy_service — path validation, access tiers, secrets guard."""

import pytest

from app.services.memory_policy_service import (
    AccessTier,
    PathValidationError,
    SecretsDetectedError,
    WriteForbiddenError,
    check_write_allowed,
    get_write_tier,
    validate_memory_path,
)

# ── Path validation ──────────────────────────────────────────────────


class TestPathValidation:
    """Tests for validate_memory_path()."""

    def test_valid_simple_path(self) -> None:
        resolved = validate_memory_path("projects/my-app/overview.md")
        assert resolved.name == "overview.md"

    def test_valid_nested_path(self) -> None:
        resolved = validate_memory_path("tasks/2026-01-01-task.md")
        assert resolved.name == "2026-01-01-task.md"

    def test_rejects_dotdot(self) -> None:
        with pytest.raises(PathValidationError, match="forbidden pattern"):
            validate_memory_path("../../etc/passwd.md")

    def test_rejects_dotdot_in_middle(self) -> None:
        with pytest.raises(PathValidationError, match="forbidden pattern"):
            validate_memory_path("projects/../etc/secret.md")

    def test_rejects_absolute_unix(self) -> None:
        with pytest.raises(PathValidationError, match="forbidden pattern"):
            validate_memory_path("/etc/passwd.md")

    def test_rejects_windows_drive(self) -> None:
        with pytest.raises(PathValidationError, match="forbidden pattern"):
            validate_memory_path("C:\\Users\\secret.md")

    def test_rejects_backslash(self) -> None:
        with pytest.raises(PathValidationError, match="forbidden pattern"):
            validate_memory_path("projects\\secret.md")

    def test_rejects_non_md(self) -> None:
        with pytest.raises(PathValidationError, match="Only .md"):
            validate_memory_path("projects/app/config.yaml")

    def test_rejects_empty_path(self) -> None:
        with pytest.raises(PathValidationError):
            validate_memory_path("")

    def test_rejects_slash_only(self) -> None:
        with pytest.raises(PathValidationError):
            validate_memory_path("/")

    def test_valid_root_file(self) -> None:
        resolved = validate_memory_path("current_state.md")
        assert resolved.name == "current_state.md"


# ── Access tiers ─────────────────────────────────────────────────────


class TestAccessTiers:
    """Tests for get_write_tier()."""

    # FORBIDDEN
    def test_obsidian_forbidden(self) -> None:
        assert get_write_tier(".obsidian/config.md") == AccessTier.FORBIDDEN

    def test_templates_forbidden(self) -> None:
        assert get_write_tier("templates/project-memory-template.md") == AccessTier.FORBIDDEN

    def test_templates_subdir_forbidden(self) -> None:
        assert get_write_tier("templates/sub/file.md") == AccessTier.FORBIDDEN

    # FREE
    def test_tasks_free(self) -> None:
        assert get_write_tier("tasks/2026-01-01-task.md") == AccessTier.FREE

    def test_project_agent_notes_free(self) -> None:
        assert get_write_tier("projects/my-app/agent_notes.md") == AccessTier.FREE

    def test_project_current_state_free(self) -> None:
        assert get_write_tier("projects/my-app/current_state.md") == AccessTier.FREE

    def test_project_tasks_free(self) -> None:
        assert get_write_tier("projects/my-app/tasks.md") == AccessTier.FREE

    def test_project_known_issues_free(self) -> None:
        assert get_write_tier("projects/my-app/known_issues.md") == AccessTier.FREE

    # APPROVAL_REQUIRED
    def test_project_overview_approval(self) -> None:
        assert get_write_tier("projects/my-app/overview.md") == AccessTier.APPROVAL_REQUIRED

    def test_project_architecture_approval(self) -> None:
        assert get_write_tier("projects/my-app/architecture.md") == AccessTier.APPROVAL_REQUIRED

    def test_project_decisions_approval(self) -> None:
        assert get_write_tier("projects/my-app/decisions.md") == AccessTier.APPROVAL_REQUIRED

    def test_root_current_state_approval(self) -> None:
        assert get_write_tier("current_state.md") == AccessTier.APPROVAL_REQUIRED

    def test_root_index_approval(self) -> None:
        assert get_write_tier("_INDEX.md") == AccessTier.APPROVAL_REQUIRED

    def test_root_readme_approval(self) -> None:
        assert get_write_tier("README.md") == AccessTier.APPROVAL_REQUIRED

    def test_decisions_approval(self) -> None:
        assert get_write_tier("decisions/0001-something.md") == AccessTier.APPROVAL_REQUIRED

    def test_agents_approval(self) -> None:
        assert get_write_tier("agents/backend.md") == AccessTier.APPROVAL_REQUIRED


# ── check_write_allowed ──────────────────────────────────────────────


class TestCheckWriteAllowed:
    """Tests for the full write permission check."""

    def test_free_write_allowed(self) -> None:
        tier = check_write_allowed("tasks/test.md", "hello world")
        assert tier == AccessTier.FREE

    def test_approval_write_blocked(self) -> None:
        with pytest.raises(WriteForbiddenError, match="requires approval"):
            check_write_allowed("current_state.md", "updated content")

    def test_approval_write_bypassed(self) -> None:
        tier = check_write_allowed(
            "current_state.md", "updated content", bypass_approval=True
        )
        assert tier == AccessTier.APPROVAL_REQUIRED

    def test_forbidden_write_blocked(self) -> None:
        with pytest.raises(WriteForbiddenError, match="forbidden"):
            check_write_allowed(".obsidian/config.md", "data")

    def test_forbidden_write_even_with_bypass(self) -> None:
        with pytest.raises(WriteForbiddenError, match="forbidden"):
            check_write_allowed(
                ".obsidian/config.md", "data", bypass_approval=True
            )

    def test_secrets_blocked(self) -> None:
        with pytest.raises(SecretsDetectedError, match="forbidden patterns"):
            check_write_allowed("tasks/test.md", "password=secret123")

    def test_invalid_path_blocked(self) -> None:
        with pytest.raises(PathValidationError):
            check_write_allowed("../../etc/passwd.md", "data")
