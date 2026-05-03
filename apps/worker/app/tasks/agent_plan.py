"""Agent plan task — generates a plan via backend runtime API and notifies.

Pipeline:
1. Call ``POST /runtime/tasks/{task_id}/plan`` on Orchestrator API.
2. Extract plan result (status, plan_text, chat_id, thread_id).
3. Dispatch ``tasks.send_notification`` to the ``notifications`` queue.
"""

from __future__ import annotations

import logging

import httpx

from app.celery_app import celery_app
from app.config import settings
from app.queues import AGENT_PLAN

logger = logging.getLogger(__name__)


def _format_plan_message(task_id: str, task_status: str, plan_text: str) -> str:
    """Build a concise Telegram notification for the plan result."""
    lines = [
        "📋 <b>Plan ready</b>",
        f"Task: <code>{task_id}</code>",
        f"Status: <b>{task_status}</b>",
    ]
    if plan_text:
        # Truncate long plans for Telegram
        preview = plan_text[:800]
        if len(plan_text) > 800:
            preview += "…"
        lines.append("")
        lines.append(preview)

    if task_status == "waiting_approval":
        lines.append("")
        lines.append("⚠️ <i>Waiting for approval to execute.</i>")
    elif task_status == "approved":
        lines.append("")
        lines.append("✅ <i>Auto-approved (low risk). Ready for execution.</i>")

    return "\n".join(lines)


@celery_app.task(
    name="tasks.agent_plan",
    queue=AGENT_PLAN,
    max_retries=settings.TASK_MAX_RETRIES,
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=settings.TASK_RETRY_BACKOFF,
    retry_backoff_max=settings.TASK_RETRY_BACKOFF_MAX,
    retry_jitter=settings.TASK_RETRY_JITTER,
)
def generate_plan(task_id: str) -> dict:
    """Generate a plan for a task and dispatch notification.

    Args:
        task_id: UUID string of the task to plan.

    Returns:
        Dict with plan result or error info.
    """
    api = settings.API_BASE_URL.rstrip("/")
    plan_url = f"{api}/runtime/tasks/{task_id}/plan"
    task_url = f"{api}/tasks/{task_id}"
    logger.info("agent_plan: task=%s — calling runtime plan endpoint", task_id)

    try:
        with httpx.Client(timeout=settings.API_TIMEOUT_SECONDS) as client:
            # Step 1: Generate plan via backend runtime
            plan_resp = client.post(plan_url)
            plan_resp.raise_for_status()
            task_data = plan_resp.json()

            # Step 2: Also fetch full task for telegram_chat_id / thread_id
            # (plan endpoint returns task but may not have all notification fields)
            task_resp = client.get(task_url)
            task_resp.raise_for_status()
            full_task = task_resp.json()

        task_status = task_data.get("status", "unknown")
        plan_text = task_data.get("plan_text", "")
        chat_id = full_task.get("telegram_chat_id")
        thread_id = full_task.get("telegram_thread_id")

        logger.info(
            "agent_plan: task=%s status=%s chat=%s thread=%s",
            task_id,
            task_status,
            chat_id,
            thread_id,
        )

        # Step 3: Dispatch notification if we have a chat_id
        if chat_id:
            notification_msg = _format_plan_message(task_id, task_status, plan_text)
            celery_app.send_task(
                "tasks.send_notification",
                kwargs={
                    "notification_type": "plan_ready",
                    "chat_id": chat_id,
                    "thread_id": thread_id,
                    "message": notification_msg,
                },
                queue="notifications",
            )
            logger.info("agent_plan: notification dispatched for task=%s", task_id)
        else:
            logger.warning("agent_plan: no chat_id for task=%s — skipping notification", task_id)

        return {
            "status": "ok",
            "task_id": task_id,
            "task_status": task_status,
            "notification_sent": chat_id is not None,
        }

    except httpx.HTTPError as exc:
        logger.warning("agent_plan: HTTP error for task=%s: %s", task_id, exc)
        return {
            "status": "error",
            "task_id": task_id,
            "error": str(exc),
        }
