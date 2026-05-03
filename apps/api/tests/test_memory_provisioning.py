"""Tests for MemoryProvisioningService."""

from pathlib import Path

import pytest

from app.schemas.memory import MemoryProvisionRequest, contains_forbidden_content
from app.services.memory_provisioning_service import (
    PROJECT_FILES,
    MemoryProvisioningService,
)


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory."""
    vault = tmp_path / ".ai_memory"
    vault.mkdir()
    (vault / "projects").mkdir()
    return vault


@pytest.fixture
def svc(tmp_vault: Path) -> MemoryProvisioningService:
    """Create a service pointed at the temp vault."""
    return MemoryProvisioningService(vault_path=str(tmp_vault))


def test_provision_creates_7_files(svc: MemoryProvisioningService, tmp_vault: Path) -> None:
    result = svc.provision_project("my-project", "My Project")

    assert result.slug == "my-project"
    assert result.created_count == 7
    assert result.skipped_count == 0
    assert len(result.files) == 7

    project_dir = tmp_vault / "projects" / "my-project"
    assert project_dir.is_dir()

    expected_files = {
        "overview.md",
        "current_state.md",
        "architecture.md",
        "decisions.md",
        "tasks.md",
        "known_issues.md",
        "agent_notes.md",
    }
    actual_files = {f.name for f in project_dir.iterdir() if f.is_file()}
    assert actual_files == expected_files


def test_provision_does_not_overwrite(svc: MemoryProvisioningService, tmp_vault: Path) -> None:
    # First provision
    svc.provision_project("demo", "Demo Project")

    # Modify a file
    overview = tmp_vault / "projects" / "demo" / "overview.md"
    overview.write_text("MODIFIED CONTENT")

    # Second provision
    result = svc.provision_project("demo", "Demo Project")
    assert result.skipped_count == 7
    assert result.created_count == 0

    # File should still have modified content
    assert overview.read_text() == "MODIFIED CONTENT"


def test_provision_template_substitution(svc: MemoryProvisioningService, tmp_vault: Path) -> None:
    svc.provision_project("test-app", "Test Application")

    overview = tmp_vault / "projects" / "test-app" / "overview.md"
    content = overview.read_text()

    assert "# Project: Test Application" in content
    assert "test-app" in content


def test_get_project_info_existing(svc: MemoryProvisioningService) -> None:
    svc.provision_project("info-test", "Info Test")

    info = svc.get_project_info("info-test")
    assert info.exists is True
    assert info.slug == "info-test"
    assert len(info.files) == 7


def test_get_project_info_nonexistent(svc: MemoryProvisioningService) -> None:
    info = svc.get_project_info("nonexistent")
    assert info.exists is False
    assert info.files == []


def test_list_projects_empty(svc: MemoryProvisioningService) -> None:
    projects = svc.list_projects()
    assert projects == []


def test_list_projects_after_provision(svc: MemoryProvisioningService) -> None:
    svc.provision_project("alpha", "Alpha")
    svc.provision_project("beta", "Beta")

    projects = svc.list_projects()
    slugs = [p.slug for p in projects]
    assert "alpha" in slugs
    assert "beta" in slugs
    assert len(projects) == 2


def test_project_files_constant_has_7_entries() -> None:
    assert len(PROJECT_FILES) == 7


def test_schema_provision_request_validates_slug() -> None:
    req = MemoryProvisionRequest(slug="my-project", name="My Project")
    assert req.slug == "my-project"


def test_schema_provision_request_rejects_bad_slug() -> None:
    with pytest.raises(Exception):
        MemoryProvisionRequest(slug="My Project!", name="Bad")


def test_contains_forbidden_content_detects_secrets() -> None:
    assert contains_forbidden_content("my api_key=secret123") is True
    assert contains_forbidden_content("password=abc123") is True
    assert contains_forbidden_content("bearer xyz") is True
    assert contains_forbidden_content("Authorization: bearer_abc123") is True
    assert contains_forbidden_content("normal text without secrets") is False
    assert contains_forbidden_content("deploy to staging") is False
    assert contains_forbidden_content("the secret garden book") is False
    assert contains_forbidden_content("-----begin private key-----") is True


def test_provision_creates_project_dir_if_missing(tmp_path: Path) -> None:
    """Service should create .ai_memory/projects/ if it doesn't exist."""
    vault = tmp_path / "new_vault"
    vault.mkdir()
    # Don't create projects/ subdirectory
    svc = MemoryProvisioningService(vault_path=str(vault))
    result = svc.provision_project("test", "Test")

    assert result.created_count == 7
    assert (vault / "projects" / "test").is_dir()
