"""Sensitive path detection for Local Runner skeleton."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path


class SensitivePathFlag(StrEnum):
    ENV_FILE = "env_file"
    PRIVATE_KEY = "private_key"
    SSH_DIR = "ssh_dir"
    CREDENTIALS = "credentials"
    GIT_CONFIG = "git_config"
    RCLONE_CONFIG = "rclone_config"
    GENERATED_DIR = "generated_dir"


_GENERATED_DIRS = {
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


def classify_path(path: Path | str) -> list[str]:
    """Classify sensitive/special path flags based on path patterns."""
    p = Path(path)
    lowered = [part.lower() for part in p.parts]
    name = p.name.lower()

    flags: set[str] = set()

    if name == ".env" or name.startswith(".env."):
        flags.add(SensitivePathFlag.ENV_FILE.value)
    if name.endswith(".pem") or name.endswith(".key") or name in {"id_rsa", "id_ed25519"}:
        flags.add(SensitivePathFlag.PRIVATE_KEY.value)
    if ".ssh" in lowered:
        flags.add(SensitivePathFlag.SSH_DIR.value)
    if name.startswith("secrets.") or name.startswith("credentials."):
        flags.add(SensitivePathFlag.CREDENTIALS.value)
    if name in {".npmrc", ".pypirc", ".netrc"}:
        flags.add(SensitivePathFlag.CREDENTIALS.value)
    if name == "config" and len(lowered) >= 2 and lowered[-2] == ".git":
        flags.add(SensitivePathFlag.GIT_CONFIG.value)
    if name == "rclone.conf":
        flags.add(SensitivePathFlag.RCLONE_CONFIG.value)
    if any(part in _GENERATED_DIRS for part in lowered):
        flags.add(SensitivePathFlag.GENERATED_DIR.value)

    return sorted(flags)


def is_sensitive_path(path: Path | str) -> bool:
    """Return whether a path matches sensitive path policy flags."""
    return bool(classify_path(path))


def explain_safety_flags(flags: list[str]) -> list[str]:
    """Convert safety flags to human-readable explanations."""
    mapping = {
        SensitivePathFlag.ENV_FILE.value: "Environment file pattern is restricted by default.",
        SensitivePathFlag.PRIVATE_KEY.value: "Private key material is restricted by default.",
        SensitivePathFlag.SSH_DIR.value: "SSH directory is restricted by default.",
        SensitivePathFlag.CREDENTIALS.value: "Credentials file pattern is restricted by default.",
        SensitivePathFlag.GIT_CONFIG.value: ".git/config is restricted unless explicitly approved.",
        SensitivePathFlag.RCLONE_CONFIG.value: "rclone.conf is restricted by default.",
        SensitivePathFlag.GENERATED_DIR.value: "Generated/heavy directory is default-deny in skeleton mode.",
    }
    return [mapping.get(flag, f"Unknown safety flag: {flag}") for flag in flags]
