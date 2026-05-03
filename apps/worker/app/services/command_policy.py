"""Command policy for WRK-03 safe execution — hardened.

Implements:
- Strict allowlist (only exact safe tool prefixes)
- Expanded denylist covering shell/chaining operators, escapes, network tools,
  privilege escalation, dangerous git commands, secret-touching patterns
- Denylist always has priority over allowlist
"""

from __future__ import annotations

import re


class CommandPolicyError(Exception):
    """Raised when command is denied by execution policy."""


# ── Strict allowlist ──────────────────────────────────────────────────
# Only these exact prefixes are allowed. No generic "python -m" blanket.

ALLOW_PREFIXES: tuple[str, ...] = (
    "pytest",
    "python -m pytest",
    "ruff",
    "ruff check",
    "python -m compileall",
    "git status",
    "git diff",
    "pip list",
    "python -m pip list",
)


# ── Expanded denylist ─────────────────────────────────────────────────

DENY_PATTERNS: tuple[re.Pattern[str], ...] = (
    # ── shell chaining / command injection (CRITICAL C-2) ──────────
    re.compile(r"&&"),
    re.compile(r";\s"),
    re.compile(r";$"),
    re.compile(r";(?!\s*\w+\s*=\s*)"),
    re.compile(r"\|(?!=)"),
    re.compile(r"\|\|"),
    re.compile(r"`[^`]+`"),
    re.compile(r"\$\([^)]+\)"),
    re.compile(r"[<>](?!\d)"),
    re.compile(r"\n"),

    # ── shell escape via interpreters (CRITICAL C-1) ────────────────
    re.compile(r"\bsh\s+-c\b", re.IGNORECASE),
    re.compile(r"\bbash\s+-c\b", re.IGNORECASE),
    re.compile(r"\bcmd\s+/c\b", re.IGNORECASE),
    re.compile(r"\bpowershell\b", re.IGNORECASE),
    re.compile(r"\bpwsh\b", re.IGNORECASE),
    re.compile(r"\bpython\s+-c\b", re.IGNORECASE),
    re.compile(r"\bpython\s+-<<", re.IGNORECASE),
    re.compile(r"\bpython3\s+-c\b", re.IGNORECASE),

    # ── network / data exfiltration (HIGH H-1) ───────────────────────
    re.compile(r"\bcurl\b", re.IGNORECASE),
    re.compile(r"\bwget\b", re.IGNORECASE),
    re.compile(r"\bnc\b", re.IGNORECASE),
    re.compile(r"\bnetcat\b", re.IGNORECASE),
    re.compile(r"\btelnet\b", re.IGNORECASE),
    re.compile(r"\bftp\b", re.IGNORECASE),
    re.compile(r"\bscp\b", re.IGNORECASE),
    re.compile(r"\brsync\b", re.IGNORECASE),

    # ── privilege escalation (HIGH H-2) ──────────────────────────────
    re.compile(r"\bsudo\b", re.IGNORECASE),
    re.compile(r"\bsu\b", re.IGNORECASE),
    re.compile(r"\bchmod\b", re.IGNORECASE),
    re.compile(r"\bchown\b", re.IGNORECASE),

    # ── system / destructive ─────────────────────────────────────────
    re.compile(r"\bdocker\b", re.IGNORECASE),
    re.compile(r"\bdocker-compose\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+compose\b", re.IGNORECASE),
    re.compile(r"\balembic\b", re.IGNORECASE),
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\bdel\s+/s\b", re.IGNORECASE),
    re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    re.compile(r"\btruncate\b", re.IGNORECASE),
    re.compile(r"\bmigrate:fresh\b", re.IGNORECASE),
    re.compile(r"\bdb:wipe\b", re.IGNORECASE),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\breboot\b", re.IGNORECASE),
    re.compile(r"\bsystemctl\b", re.IGNORECASE),
    re.compile(r"\bservice\s+\w+\s+(start|stop|restart)\b", re.IGNORECASE),
    re.compile(r"\brestart\b", re.IGNORECASE),

    # ── git dangerous operations ─────────────────────────────────────
    re.compile(r"git\s+reset\s+--hard", re.IGNORECASE),
    re.compile(r"git\s+clean\b", re.IGNORECASE),
    re.compile(r"git\s+push\s+--force", re.IGNORECASE),
    re.compile(r"git\s+push\s+-f\b", re.IGNORECASE),
    re.compile(r"git\s+checkout\b", re.IGNORECASE),
    re.compile(r"git\s+clone\b", re.IGNORECASE),
    re.compile(r"git\s+fetch\b", re.IGNORECASE),
    re.compile(r"git\s+pull\b", re.IGNORECASE),
    re.compile(r"git\s+push\b", re.IGNORECASE),
    re.compile(r"git\s+merge\b", re.IGNORECASE),
    re.compile(r"git\s+rebase\b", re.IGNORECASE),
    re.compile(r"git\s+commit\b", re.IGNORECASE),

    # ── deploy / env / secrets ───────────────────────────────────────
    re.compile(r"\bdeploy\b", re.IGNORECASE),
    re.compile(r"\b\.env\b", re.IGNORECASE),
    re.compile(r"\btoken\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
)


def validate_command(command: str) -> None:
    """Validate command against denylist and allowlist.

    Denylist has priority: if ANY deny pattern matches, command is
    rejected regardless of allowlist.

    After denylist check, command must match one of the allowlist
    prefixes.
    """
    normalized = command.strip()
    if not normalized:
        raise CommandPolicyError("Command is empty")

    # Denylist check — first priority
    for pattern in DENY_PATTERNS:
        if pattern.search(normalized):
            raise CommandPolicyError(
                f"Command denied by policy pattern: {pattern.pattern}"
            )

    # Allowlist check — second priority
    if not any(normalized.startswith(prefix) for prefix in ALLOW_PREFIXES):
        raise CommandPolicyError(
            "Command is not in allowlist"
        )
