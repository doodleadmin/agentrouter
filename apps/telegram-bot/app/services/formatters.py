"""TG-03: Formatters for Telegram messages — task cards, approval cards, plan excerpts."""

from __future__ import annotations

from typing import Any

# ── emoji maps ─────────────────────────────────────────────────────────

_STATUS_EMOJI: dict[str, str] = {
    "created": "🆕",
    "routed": "🚦",
    "planning": "🤔",
    "waiting_approval": "⏳",
    "approved": "✅",
    "running": "🏃",
    "tests_running": "🧪",
    "pr_created": "📬",
    "deploying_staging": "🚀",
    "deploying_production": "🔥",
    "completed": "🏁",
    "failed": "❌",
    "cancelled": "🚫",
}

_RISK_EMOJI: dict[str, str] = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "critical": "🔴",
}

_APPROVAL_STATUS_EMOJI: dict[str, str] = {
    "pending": "⏳",
    "approved": "✅",
    "rejected": "❌",
}


# ── format helpers ─────────────────────────────────────────────────────

def format_task_card(task: dict[str, Any]) -> str:
    """Format a task for display in Telegram as an HTML card.

    Expected keys: id, external_id, title, status, risk_level, intent,
                   project_id, agent_id, plan_text, result_summary,
                   created_at, updated_at.
    """
    status = task.get("status", "unknown")
    risk = task.get("risk_level", "low")
    status_emoji = _STATUS_EMOJI.get(status, "❓")
    risk_emoji = _RISK_EMOJI.get(risk, "⚪")

    lines = [
        f"{status_emoji} <b>Task {task.get('external_id', 'N/A')}</b>",
        f"Status: <code>{status}</code>  {risk_emoji} Risk: <code>{risk}</code>",
    ]

    title = task.get("title", "")
    if title:
        lines.append(f"📝 <i>{_escape_html(title[:200])}</i>")

    if task.get("project_id"):
        lines.append(f"📦 Project: <code>{task['project_id']}</code>")
    if task.get("agent_id"):
        lines.append(f"🤖 Agent: <code>{task['agent_id']}</code>")
    if task.get("intent"):
        lines.append(f"🎯 Intent: <code>{_escape_html(task['intent'])}</code>")

    plan = task.get("plan_text")
    if plan:
        has_plan = "✅ Plan available" if len(plan) > 10 else "⏳ Plan pending"
        lines.append(has_plan)

    result = task.get("result_summary")
    if result:
        lines.append(f"📋 Result: {_escape_html(result[:200])}")

    lines.append(f"🕐 Updated: <i>{_format_ts(task.get('updated_at', ''))}</i>")

    return "\n".join(lines)


def format_approval_card(task: dict[str, Any], approval: dict[str, Any]) -> str:
    """Format an approval request for display.

    Expected approval keys: id, action, status, reason, payload, decided_at.
    """
    action = approval.get("action", "unknown")
    status = approval.get("status", "pending")
    approval_emoji = _APPROVAL_STATUS_EMOJI.get(status, "❓")

    lines = [
        "🔐 <b>Approval Request</b>",
        f"Task: <b>{task.get('external_id', 'N/A')}</b>",
        f"Action: <code>{_escape_html(action)}</code>",
        f"Status: {approval_emoji} <code>{status}</code>",
    ]

    risk = task.get("risk_level", "low")
    risk_emoji = _RISK_EMOJI.get(risk, "⚪")
    lines.append(f"Risk: {risk_emoji} <code>{risk}</code>")

    reason = approval.get("reason")
    if reason:
        lines.append(f"Reason: <i>{_escape_html(reason[:300])}</i>")

    payload = approval.get("payload")
    if payload and isinstance(payload, dict) and len(payload) > 0:
        lines.append(f"Payload: <code>{_escape_html(str(payload)[:200])}</code>")

    decided = approval.get("decided_at")
    if decided:
        lines.append(f"Decided: <i>{_format_ts(decided)}</i>")

    return "\n".join(lines)


def format_plan_excerpt(plan_text: str | None, max_len: int = 500) -> str:
    """Return a truncated plan excerpt with a marker if truncated."""
    if not plan_text:
        return "<i>No plan available yet.</i>"

    if len(plan_text) <= max_len:
        return _escape_html(plan_text)

    excerpt = plan_text[:max_len]
    return _escape_html(excerpt) + f"\n\n<i>... (plan truncated, {len(plan_text) - max_len} more chars)</i>"


def format_error_message(error_type: str, details: str | None = None) -> str:
    """Return a safe user-facing error message."""
    base = f"⚠️ <b>{_escape_html(error_type)}</b>"
    if details:
        base += f"\n<i>{_escape_html(details[:300])}</i>"
    return base


# ── internal helpers ───────────────────────────────────────────────────

def _escape_html(text: str) -> str:
    """Escape HTML special chars for Telegram HTML parse mode."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_ts(ts: str) -> str:
    """Format ISO timestamp to a readable short form."""
    if not ts:
        return "N/A"
    try:
        # ISO format: 2026-05-05T12:34:56.789+00:00 or 2026-05-05T12:34:56.789
        parts = ts.split("T")
        if len(parts) == 2:
            time_part = parts[1].split(".")[0].split("+")[0].split("Z")[0]
            return f"{parts[0]} {time_part}"
        return ts[:19] if len(ts) >= 19 else ts
    except (ValueError, IndexError):
        return ts[:19] if len(ts) >= 19 else ts
