from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentrouter_runner.paths import PathOutsideRootError, safe_relative_path, validate_root, resolve_requested_path


def test_validate_root_ok(tmp_path: Path) -> None:
    assert validate_root(tmp_path) == tmp_path.resolve()


def test_validate_root_fail_for_missing(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        validate_root(tmp_path / "missing")


def test_resolve_requested_path_blocks_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathOutsideRootError):
        resolve_requested_path(tmp_path, "../outside")


def test_resolve_requested_path_blocks_absolute_outside(tmp_path: Path) -> None:
    if os.name == "nt":
        candidate = Path("C:/Windows")
        if candidate.exists() and candidate.drive != tmp_path.drive:
            with pytest.raises(PathOutsideRootError):
                resolve_requested_path(tmp_path, candidate)
            return
    outside = tmp_path.parent / "outside"
    with pytest.raises(PathOutsideRootError):
        resolve_requested_path(tmp_path, outside)


def test_safe_relative_path(tmp_path: Path) -> None:
    child = tmp_path / "dir" / "file.txt"
    resolved = resolve_requested_path(tmp_path, child)
    assert safe_relative_path(tmp_path, resolved) == "dir/file.txt"


def test_symlink_escape_detected_when_supported(tmp_path: Path) -> None:
    target_outside = tmp_path.parent / "outside-target"
    target_outside.mkdir(exist_ok=True)
    link = tmp_path / "escape"
    try:
        link.symlink_to(target_outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not supported in this environment")

    with pytest.raises(PathOutsideRootError):
        resolve_requested_path(tmp_path, "escape/secret.txt")
