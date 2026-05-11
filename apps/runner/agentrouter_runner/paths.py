"""Path safety helpers for Local Runner skeleton."""

from __future__ import annotations

import os
from pathlib import Path


class RunnerPathError(ValueError):
    """Base path-related error for runner path utilities."""


class RootValidationError(RunnerPathError):
    """Raised when root is missing or invalid."""


class PathOutsideRootError(RunnerPathError):
    """Raised when requested path escapes allowed root."""


def validate_root(root: Path | str) -> Path:
    """Validate and normalize allowed root path."""
    root_path = Path(root).expanduser()
    if not root_path.exists():
        raise RootValidationError(f"Root does not exist: {root_path}")
    if not root_path.is_dir():
        raise RootValidationError(f"Root is not a directory: {root_path}")
    return root_path.resolve()


def is_inside_root(root: Path | str, resolved_path: Path | str) -> bool:
    """Check whether path is inside root using normalized common path."""
    root_resolved = Path(root).resolve()
    path_resolved = Path(resolved_path).resolve(strict=False)

    root_norm = os.path.normcase(str(root_resolved))
    path_norm = os.path.normcase(str(path_resolved))
    try:
        return os.path.commonpath([root_norm, path_norm]) == root_norm
    except ValueError:
        # Different drives on Windows are never inside root.
        return False


def resolve_requested_path(root: Path | str, requested: Path | str) -> Path:
    """Resolve requested path under root and enforce confinement."""
    root_resolved = validate_root(root)
    requested_path = Path(requested)

    if requested_path.is_absolute():
        candidate = requested_path
    else:
        candidate = root_resolved / requested_path

    # strict=False keeps support for non-existing targets while still
    # resolving existing symlink/junction ancestors where possible.
    resolved = candidate.resolve(strict=False)
    if not is_inside_root(root_resolved, resolved):
        raise PathOutsideRootError(
            f"Requested path is outside allowed root: {requested_path}"
        )
    return resolved


def safe_relative_path(root: Path | str, resolved_path: Path | str) -> str:
    """Return a safe relative path representation from root."""
    root_resolved = validate_root(root)
    path_resolved = Path(resolved_path).resolve(strict=False)
    if not is_inside_root(root_resolved, path_resolved):
        raise PathOutsideRootError(f"Path outside root: {path_resolved}")

    rel = path_resolved.relative_to(root_resolved)
    text = rel.as_posix()
    return text if text else "."
