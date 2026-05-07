"""TG-03/TG-06: Inline keyboard builders for task cards and callbacks."""

from __future__ import annotations

import hashlib
import hmac
import time

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ── callback protocol helpers ──────────────────────────────────────────

_CALLBACK_VERSION = "v1"
_CALLBACK_ALIASES = {
    "approve": "a",
    "reject": "r",
    "refresh": "f",
    "show_plan": "p",
    "show_task": "t",
}
_BASE36_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _to_base36(value: int) -> str:
    """Encode a non-negative integer as lowercase base36."""
    if value < 0:
        raise ValueError("base36 value must be non-negative")
    if value == 0:
        return "0"
    chars: list[str] = []
    while value:
        value, rem = divmod(value, 36)
        chars.append(_BASE36_ALPHABET[rem])
    return "".join(reversed(chars))


def _make_callback_data(
    action: str,
    task_external_id: str,
    approval_id: str = "none",
    rev: int = 1,
    ttl: int = 300,
    secret: str = "",
) -> str:
    """Build compact signed callback_data: v1:<alias>:<external_id>:<exp36>:<sig16>."""
    del approval_id, rev  # TG-06 compact protocol intentionally excludes these fields.

    alias = _CALLBACK_ALIASES[action]
    exp_base36 = _to_base36(int(time.time()) + ttl)
    signing_payload = f"{_CALLBACK_VERSION}|{alias}|{task_external_id}|{exp_base36}"
    sig = hmac.new(
        secret.encode("utf-8") if secret else b"",
        signing_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]
    callback_data = f"{_CALLBACK_VERSION}:{alias}:{task_external_id}:{exp_base36}:{sig}"
    if len(callback_data.encode("utf-8")) > 64:
        raise ValueError("callback_data exceeds Telegram 64-byte limit")
    return callback_data


def _get_callback_secret() -> str:
    """Get callback secret from settings (lazy import to avoid circular)."""
    try:
        from app.config import settings
        return settings.CALLBACK_SECRET
    except Exception:
        return ""


# ── keyboard builders ──────────────────────────────────────────────────


def build_task_keyboard(
    task_id: str,
    task_status: str,
    has_pending_approval: bool = False,
    approval_id: str | None = None,
    has_plan: bool = False,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for a task status card.

    Shows context-appropriate buttons based on task state:
    - Approve/Reject: only if has_pending_approval
    - Show plan: only if has_plan
    - Refresh: always
    """
    buttons: list[list[InlineKeyboardButton]] = []
    secret = _get_callback_secret()

    # Approval actions
    if has_pending_approval and approval_id:
        approve_cb = _make_callback_data("approve", task_id, approval_id=approval_id, secret=secret)
        reject_cb = _make_callback_data("reject", task_id, approval_id=approval_id, secret=secret)
        buttons.append([
            InlineKeyboardButton(text="✅ Approve", callback_data=approve_cb),
            InlineKeyboardButton(text="❌ Reject", callback_data=reject_cb),
        ])

    # Plan action
    if has_plan:
        plan_cb = _make_callback_data("show_plan", task_id, secret=secret)
        buttons.append([
            InlineKeyboardButton(text="📋 Show Plan", callback_data=plan_cb),
        ])

    # Refresh always present
    refresh_cb = _make_callback_data("refresh", task_id, secret=secret)
    buttons.append([
        InlineKeyboardButton(text="🔄 Refresh", callback_data=refresh_cb),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_approval_keyboard(
    task_id: str,
    approval_id: str,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for an approval request card.

    Shows Approve and Reject buttons with signed callback data.
    """
    secret = _get_callback_secret()
    approve_cb = _make_callback_data("approve", task_id, approval_id=approval_id, secret=secret)
    reject_cb = _make_callback_data("reject", task_id, approval_id=approval_id, secret=secret)
    refresh_cb = _make_callback_data("refresh", task_id, approval_id=approval_id, secret=secret)

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=approve_cb),
            InlineKeyboardButton(text="❌ Reject", callback_data=reject_cb),
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data=refresh_cb),
        ],
    ])


def build_plan_keyboard(
    task_id: str,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for plan display.

    Shows Refresh button for checking updated plan status.
    """
    secret = _get_callback_secret()
    refresh_cb = _make_callback_data("refresh", task_id, secret=secret)
    task_cb = _make_callback_data("show_task", task_id, secret=secret)

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Show Task", callback_data=task_cb),
            InlineKeyboardButton(text="🔄 Refresh", callback_data=refresh_cb),
        ],
    ])
