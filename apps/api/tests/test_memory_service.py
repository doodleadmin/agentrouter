"""Tests for memory_service — CRUD operations on .ai_memory vault."""

import pytest

from app.services.memory_policy_service import PathValidationError, WriteForbiddenError
from app.services.memory_service import MemoryFileNotFoundError, MemoryService


@pytest.fixture
def tmp_vault(tmp_path):
    """Create a temp vault with some test files."""
    vault = tmp_path / ".ai_memory"
    vault.mkdir()

    # Create structure
    (vault / "projects" / "test-app").mkdir(parents=True)
    (vault / "tasks").mkdir()
    (vault / "decisions").mkdir()
    (vault / "templates").mkdir()

    # Create test files
    (vault / "current_state.md").write_text("# Current State\n\nOld content.", encoding="utf-8")
    (vault / "projects" / "test-app" / "overview.md").write_text(
        "# Test App\n", encoding="utf-8"
    )
    (vault / "projects" / "test-app" / "agent_notes.md").write_text(
        "# Notes\n", encoding="utf-8"
    )
    (vault / "tasks" / "2026-01-01-task.md").write_text(
        "# Task Summary\n", encoding="utf-8"
    )

    return vault


@pytest.fixture
def svc(tmp_vault):
    return MemoryService(vault_path=str(tmp_vault))


# ── Read ─────────────────────────────────────────────────────────────


class TestRead:
    def test_read_existing_file(self, svc: MemoryService) -> None:
        result = svc.read_file("current_state.md")
        assert result.path == "current_state.md"
        assert "Old content" in result.content
        assert result.size > 0
        assert result.modified_at != ""

    def test_read_nested_file(self, svc: MemoryService) -> None:
        result = svc.read_file("projects/test-app/overview.md")
        assert "Test App" in result.content

    def test_read_nonexistent(self, svc: MemoryService) -> None:
        with pytest.raises(MemoryFileNotFoundError):
            svc.read_file("nonexistent.md")

    def test_read_invalid_path(self, svc: MemoryService) -> None:
        with pytest.raises(PathValidationError):
            svc.read_file("../../etc/passwd.md")


# ── Write ────────────────────────────────────────────────────────────


class TestWrite:
    def test_write_free_file(self, svc: MemoryService) -> None:
        result = svc.write_file("tasks/new-task.md", "# New Task\n")
        assert result.status == "written"
        assert result.access_tier == "free"

    def test_write_creates_parent_dirs(self, svc: MemoryService) -> None:
        result = svc.write_file("projects/new-app/agent_notes.md", "# Notes\n")
        assert result.status == "written"

    def test_write_approval_blocked(self, svc: MemoryService) -> None:
        with pytest.raises(WriteForbiddenError, match="requires approval"):
            svc.write_file("current_state.md", "# Updated\n")

    def test_write_approval_bypassed(self, svc: MemoryService) -> None:
        result = svc.write_file(
            "current_state.md", "# Updated\n", bypass_approval=True
        )
        assert result.status == "written"

    def test_write_secrets_blocked(self, svc: MemoryService) -> None:
        with pytest.raises(Exception, match="forbidden"):
            svc.write_file("tasks/test.md", "password=secret123")

    def test_write_forbidden_path(self, svc: MemoryService) -> None:
        with pytest.raises(WriteForbiddenError, match="forbidden"):
            svc.write_file("templates/template.md", "content")

    def test_write_overwrites_existing(self, svc: MemoryService) -> None:
        svc.write_file("projects/test-app/agent_notes.md", "Replaced content", bypass_approval=False)
        result = svc.read_file("projects/test-app/agent_notes.md")
        assert result.content == "Replaced content"


# ── Append ───────────────────────────────────────────────────────────


class TestAppend:
    def test_append_to_existing(self, svc: MemoryService) -> None:
        result = svc.append_file("tasks/2026-01-01-task.md", "\n## New Section\n")
        assert result.status == "appended"
        assert result.access_tier == "free"

        content = svc.read_file("tasks/2026-01-01-task.md").content
        assert "New Section" in content
        assert "Task Summary" in content

    def test_append_creates_new_file(self, svc: MemoryService) -> None:
        result = svc.append_file("tasks/new-file.md", "# New\n")
        assert result.status == "appended"

    def test_append_approval_blocked(self, svc: MemoryService) -> None:
        with pytest.raises(WriteForbiddenError, match="requires approval"):
            svc.append_file("decisions/adr.md", "## ADR\n")


# ── List ─────────────────────────────────────────────────────────────


class TestList:
    def test_list_all(self, svc: MemoryService) -> None:
        result = svc.list_files()
        assert result.total >= 4
        assert any("current_state.md" in f for f in result.files)
        assert any("overview.md" in f for f in result.files)

    def test_list_by_project(self, svc: MemoryService) -> None:
        result = svc.list_files(project_slug="test-app")
        assert result.project_slug == "test-app"
        assert any("overview.md" in f for f in result.files)
        assert any("agent_notes.md" in f for f in result.files)

    def test_list_by_prefix(self, svc: MemoryService) -> None:
        result = svc.list_files(prefix="tasks")
        assert result.total >= 1
        assert all(f.startswith("tasks/") for f in result.files)

    def test_list_nonexistent_prefix_empty(self, svc: MemoryService) -> None:
        result = svc.list_files(prefix="nonexistent")
        assert result.total == 0

    def test_list_skips_hidden(self, svc: MemoryService) -> None:
        # Create .obsidian directory
        vault = svc.vault_path
        (vault / ".obsidian").mkdir(exist_ok=True)
        (vault / ".obsidian" / "config.md").write_text("cfg", encoding="utf-8")
        result = svc.list_files()
        assert not any(".obsidian" in f for f in result.files)

    def test_list_invalid_prefix_blocked(self, svc: MemoryService) -> None:
        with pytest.raises(PathValidationError):
            svc.list_files(prefix="../../etc")


# ── Access tier ──────────────────────────────────────────────────────


class TestGetAccessTier:
    def test_free_tier(self, svc: MemoryService) -> None:
        tier = svc.get_access_tier("tasks/test.md")
        assert tier.value == "free"

    def test_approval_tier(self, svc: MemoryService) -> None:
        tier = svc.get_access_tier("current_state.md")
        assert tier.value == "approval_required"

    def test_forbidden_tier(self, svc: MemoryService) -> None:
        tier = svc.get_access_tier("templates/something.md")
        assert tier.value == "forbidden"
