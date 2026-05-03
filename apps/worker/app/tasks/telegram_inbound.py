"""Telegram inbound message processing — stub.

In the future this will:
1. Receive raw Telegram message data.
2. Call Orchestrator API to classify intent / detect project / agent.
3. Route to agent_plan or agent_execute queue.

For WRK-01 this is a stub that logs and returns.
"""

import logging

from app.celery_app import celery_app
from app.config import settings
from app.queues import TELEGRAM_INBOUND

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.telegram_inbound",
    queue=TELEGRAM_INBOUND,
    max_retries=settings.TASK_MAX_RETRIES,
    autoretry_for=(Exception,),
    retry_backoff=settings.TASK_RETRY_BACKOFF,
    retry_backoff_max=settings.TASK_RETRY_BACKOFF_MAX,
    retry_jitter=settings.TASK_RETRY_JITTER,
)
def process_telegram_inbound(chat_id: int, thread_id: int | None, text: str, user_id: int | None = None) -> dict:
    """Process an inbound Telegram message (stub).

    Returns a summary dict instead of performing real actions.
    """
    logger.info("telegram_inbound: chat_id=%s thread_id=%s user=%s text=%.60s", chat_id, thread_id, user_id, text)

    # Stub: in the future this will call the backend API
    # to classify intent, detect project/agent, and create a task.
    return {
        "status": "stub",
        "message": "telegram_inbound processed (stub — no real action taken)",
        "chat_id": chat_id,
        "thread_id": thread_id,
    }
