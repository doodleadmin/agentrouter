"""TG-03: Inline keyboard builders for task cards, approvals, and plan display."""

from __future__ import annotations

import hashlib
import hmac
import time

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ── callback protocol helpers ──────────────────────────────────────────

_CALLBACK_FIELD_SEP = "|"
_CALLBACK_VERSION = 1  # v1 protocol: version|action|task_id|approval_id|rev|exp|sig


def _make_callback_data(
    action: str,
    task_id: str,
    approval_id: str = "none",
    rev: int = 1,
    ttl: int = 300,
    secret: str = "",
) -> str:
    """Build a signed v1 callback_data string with HMAC-SHA256 signature."""
    exp = int(time.time()) + ttl
    base = f"{_CALLBACK_VERSION}{_CALLBACK_FIELD_SEP}{action}{_CALLBACK_FIELD_SEP}{task_id}{_CALLBACK_FIELD_SEP}{approval_id}{_CALLBACK_FIELD_SEP}{rev}{_CALLBACK_FIELD_SEP}{exp}"
    sig = hmac.new(
        secret.encode("utf-8") if secret else b"",
        base.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{base}{_CALLBACK_FIELD_SEP}{sig}"


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
