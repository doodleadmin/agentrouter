from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    runner_path = str((cwd / "apps" / "runner").resolve())
    env["PYTHONPATH"] = runner_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(
        [sys.executable, "-m", "agentrouter_runner", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_status_ok_and_no_env_names(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    proc = _run_cli(["--root", str(tmp_path), "status"], repo_root)
    assert proc.returncode == 0
    assert "runner_mode" in proc.stdout
    for marker in ["TELEGRAM_BOT_TOKEN", "SESSION_TOKEN", "INITDATA", "AWS_SECRET_ACCESS_KEY"]:
        assert marker not in proc.stdout


def test_doctor_fail_for_missing_root(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    missing = tmp_path / "missing"
    proc = _run_cli(["--root", str(missing), "doctor"], repo_root)
    assert proc.returncode == 1
    assert "overall" in proc.stdout


def test_check_path_success_and_block_outside(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    inside = _run_cli(["--root", str(tmp_path), "check-path", "--path", "folder/file.txt"], repo_root)
    assert inside.returncode == 0
    assert "allowed" in inside.stdout

    outside = _run_cli(["--root", str(tmp_path), "check-path", "--path", "../outside"], repo_root)
    assert outside.returncode == 2
    assert "PathOutsideRootError" in outside.stdout


def test_discovery_commands_smoke(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    (tmp_path / "proj1" / "src").mkdir(parents=True)
    (tmp_path / "proj1" / "src" / "main.py").write_text("print('x')", encoding="utf-8")
    (tmp_path / "proj2").mkdir()

    list_proc = _run_cli(["--json", "--root", str(tmp_path), "list-projects"], repo_root)
    assert list_proc.returncode == 0
    assert '"proj1"' in list_proc.stdout
    assert '"proj2"' in list_proc.stdout

    tree_proc = _run_cli(["--json", "--root", str(tmp_path), "tree", "--project", "proj1", "--max-depth", "2"], repo_root)
    assert tree_proc.returncode == 0
    assert '"project": "proj1"' in tree_proc.stdout
    assert '"relative_path": "proj1/src/main.py"' in tree_proc.stdout

    missing_tree = _run_cli(["--root", str(tmp_path), "tree", "--project", "missing"], repo_root)
    assert missing_tree.returncode == 2
    assert "FileNotFoundError" in missing_tree.stdout

    stat_proc = _run_cli(["--json", "--root", str(tmp_path), "stat", "--path", "proj1/src/main.py"], repo_root)
    assert stat_proc.returncode == 0
    assert '"is_file": true' in stat_proc.stdout

    blocked = _run_cli(["--root", str(tmp_path), "stat", "--path", "../outside"], repo_root)
    assert blocked.returncode == 2
    assert "PathOutsideRootError" in blocked.stdout
