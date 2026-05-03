"""Notifications task — sends messages to Telegram topics via Notifier adapter.

Uses ``Notifier`` protocol so it can be tested with ``StubNotifier`` and
swapped to ``TelegramNotifier`` in production.
"""

from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.config import settings
from app.queues import NOTIFICATIONS
from app.services.notifier import get_notifier

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.send_notification",
    queue=NOTIFICATIONS,
    max_retries=settings.TASK_MAX_RETRIES,
    autoretry_for=(Exception,),
    retry_backoff=settings.TASK_RETRY_BACKOFF,
    retry_backoff_max=settings.TASK_RETRY_BACKOFF_MAX,
    retry_jitter=settings.TASK_RETRY_JITTER,
)
def send_notification(
    notification_type: str,
    chat_id: int | None = None,
    thread_id: int | None = None,
    message: str = "",
) -> dict:
    """Send a notification to a Telegram topic.

    Args:
        notification_type: Type of notification (plan_ready, task_created, etc.).
        chat_id: Telegram chat ID.
        thread_id: Telegram thread (message_thread_id) for forum topics.
        message: Notification text (supports HTML parse_mode).

    Returns:
        Result dict with status and notification details.
    """
    logger.info(
        "send_notification: type=%s chat=%s thread=%s",
        notification_type,
        chat_id,
        thread_id,
    )

    if chat_id is None:
        logger.warning("send_notification: no chat_id — skipping")
        return {
            "status": "skipped",
            "reason": "no chat_id",
            "notification_type": notification_type,
        }

    notifier = get_notifier()
    try:
        result = notifier.send(chat_id=chat_id, thread_id=thread_id, text=message)
        return {
            "status": "ok",
            "notification_type": notification_type,
            "chat_id": chat_id,
            "thread_id": thread_id,
            "result": result,
        }
    except Exception as exc:
        logger.error(
            "send_notification: failed type=%s chat=%s: %s",
            notification_type,
            chat_id,
            exc,
        )
        return {
            "status": "error",
            "notification_type": notification_type,
            "chat_id": chat_id,
            "error": str(exc),
        }
