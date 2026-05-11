"""Read-only project discovery helpers for Local Runner."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .paths import resolve_requested_path, safe_relative_path, validate_root
from .safety import classify_path


@dataclass(slots=True)
class ProjectInfo:
    name: str
    path: str
    relative_path: str
    exists: bool
    is_dir: bool
    mtime: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class TreeEntry:
    name: str
    path: str
    relative_path: str
    depth: int
    exists: bool
    is_dir: bool
    is_file: bool
    extension: str
    size: int | None
    mtime: str | None
    flags: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class PathStat:
    requested: str
    path: str
    relative_path: str
    exists: bool
    is_dir: bool
    is_file: bool
    extension: str
    size: int | None
    mtime: str | None
    flags: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _mtime_iso(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _skip_entry(path: Path) -> bool:
    return "generated_dir" in classify_path(path)


def list_projects(root: Path) -> list[ProjectInfo]:
    root_resolved = validate_root(root)
    projects: list[ProjectInfo] = []
    for entry in sorted(root_resolved.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        if _skip_entry(entry):
            continue
        projects.append(
            ProjectInfo(
                name=entry.name,
                path=str(entry.resolve(strict=False)),
                relative_path=safe_relative_path(root_resolved, entry),
                exists=entry.exists(),
                is_dir=entry.is_dir(),
                mtime=_mtime_iso(entry),
            )
        )
    return projects


def build_tree(root: Path, project: str, max_depth: int = 3) -> list[TreeEntry]:
    root_resolved = validate_root(root)
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    project_path = resolve_requested_path(root_resolved, project)
    if not project_path.exists() or not project_path.is_dir():
        raise FileNotFoundError(f"Project not found under root: {project}")

    start_depth = len(project_path.parts)
    entries: list[TreeEntry] = []

    def walk(current: Path) -> None:
        depth = len(current.parts) - start_depth
        if depth > max_depth:
            return
        if current != project_path:
            flags = classify_path(current)
            entries.append(
                TreeEntry(
                    name=current.name,
                    path=str(current.resolve(strict=False)),
                    relative_path=safe_relative_path(root_resolved, current),
                    depth=depth,
                    exists=current.exists(),
                    is_dir=current.is_dir(),
                    is_file=current.is_file(),
                    extension=current.suffix.lower(),
                    size=current.stat().st_size if current.exists() and current.is_file() else None,
                    mtime=_mtime_iso(current),
                    flags=flags,
                )
            )

        if depth == max_depth or not current.is_dir():
            return

        for child in sorted(current.iterdir(), key=lambda p: p.name.lower()):
            resolved_child = resolve_requested_path(root_resolved, child)
            if _skip_entry(resolved_child):
                continue
            walk(resolved_child)

    walk(project_path)
    return entries


def stat_path(root: Path, requested_path: str) -> PathStat:
    root_resolved = validate_root(root)
    resolved = resolve_requested_path(root_resolved, requested_path)
    flags = classify_path(resolved)

    return PathStat(
        requested=requested_path,
        path=str(resolved),
        relative_path=safe_relative_path(root_resolved, resolved),
        exists=resolved.exists(),
        is_dir=resolved.is_dir(),
        is_file=resolved.is_file(),
        extension=resolved.suffix.lower(),
        size=resolved.stat().st_size if resolved.exists() and resolved.is_file() else None,
        mtime=_mtime_iso(resolved),
        flags=flags,
    )
