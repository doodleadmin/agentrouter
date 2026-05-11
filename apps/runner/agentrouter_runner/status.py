"""Status model for Local Runner skeleton mode."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from . import __version__


@dataclass(slots=True)
class RunnerStatus:
    runner_mode: str
    root: str
    root_exists: bool
    root_is_dir: bool
    root_valid: bool
    cloud_connection: str
    pairing: str
    heartbeat: str
    file_content_reads: str
    file_writes: str
    command_execution: str
    opencode: str
    safety_mode: str
    version: str

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)


def build_status(root: Path) -> RunnerStatus:
    exists = root.exists()
    is_dir = root.is_dir()
    valid = exists and is_dir
    return RunnerStatus(
        runner_mode="skeleton",
        root=str(root),
        root_exists=exists,
        root_is_dir=is_dir,
        root_valid=valid,
        cloud_connection="disabled",
        pairing="disabled",
        heartbeat="disabled",
        file_content_reads="disabled",
        file_writes="disabled",
        command_execution="disabled",
        opencode="disabled",
        safety_mode="strict",
        version=__version__,
    )
