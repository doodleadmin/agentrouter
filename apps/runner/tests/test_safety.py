from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentrouter_runner.safety import classify_path, explain_safety_flags, is_sensitive_path


def test_classify_sensitive_patterns() -> None:
    assert "env_file" in classify_path(".env")
    assert "env_file" in classify_path(".env.local")
    assert "private_key" in classify_path("keys/id_rsa")
    assert "private_key" in classify_path("certs/server.pem")
    assert "ssh_dir" in classify_path(".ssh/config")
    assert "credentials" in classify_path("credentials.prod")
    assert "credentials" in classify_path(".npmrc")
    assert "git_config" in classify_path("repo/.git/config")
    assert "rclone_config" in classify_path("rclone.conf")
    assert "generated_dir" in classify_path("frontend/node_modules/pkg/index.js")


def test_is_sensitive_path() -> None:
    assert is_sensitive_path(".env") is True
    assert is_sensitive_path("src/main.py") is False


def test_explain_flags() -> None:
    explanations = explain_safety_flags(["env_file", "generated_dir"])
    assert len(explanations) == 2
    assert any("Environment" in item for item in explanations)
