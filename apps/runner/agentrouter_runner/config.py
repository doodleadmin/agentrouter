"""Configuration model for Local Runner skeleton CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RunnerConfig:
    """CLI runtime configuration."""

    root: Path
    json_output: bool = False
