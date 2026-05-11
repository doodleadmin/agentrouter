from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentrouter_runner.discovery import build_tree, list_projects, stat_path
from agentrouter_runner.paths import PathOutsideRootError


def test_list_projects_only_top_level_dirs_stable_order(tmp_path: Path) -> None:
    (tmp_path / "zeta").mkdir()
    (tmp_path / "alpha").mkdir()
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")

    items = list_projects(tmp_path)
    assert [item.name for item in items] == ["alpha", "zeta"]
    assert all(item.is_dir for item in items)


def test_tree_depth_limit_and_skip_generated_dirs(tmp_path: Path) -> None:
    project = tmp_path / "project-a"
    (project / "src" / "api").mkdir(parents=True)
    (project / "src" / "api" / "main.py").write_text("print('ok')", encoding="utf-8")
    (project / "node_modules" / "pkg").mkdir(parents=True)
    (project / "node_modules" / "pkg" / "index.js").write_text("x", encoding="utf-8")

    items = build_tree(tmp_path, "project-a", max_depth=1)
    rels = [item.relative_path for item in items]
    assert "project-a/src" in rels
    assert "project-a/src/api" not in rels
    assert all("node_modules" not in rel for rel in rels)


def test_tree_missing_project_returns_clean_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_tree(tmp_path, "missing", max_depth=2)


def test_stat_inside_root_and_outside_blocked(tmp_path: Path) -> None:
    file_path = tmp_path / "project-a" / "README.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("hello", encoding="utf-8")

    inside = stat_path(tmp_path, "project-a/README.md")
    assert inside.exists is True
    assert inside.is_file is True
    assert inside.relative_path == "project-a/README.md"

    with pytest.raises(PathOutsideRootError):
        stat_path(tmp_path, "../outside")
