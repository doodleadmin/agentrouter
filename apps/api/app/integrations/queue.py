"""Thin Celery task dispatcher for the API layer.

Uses ``send_task`` so the API does not need to import worker task code.
Only the broker URL is required.
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

_sender: Celery | None = None


def _get_sender() -> Celery:
    global _sender
    if _sender is None:
        _sender = Celery(broker=settings.CELERY_BROKER_URL)
    return _sender


def enqueue_agent_plan(task_id: str) -> None:
    """Send *tasks.agent_plan* job to the ``agent_plan`` queue."""
    _get_sender().send_task(
        "tasks.agent_plan",
        args=[task_id],
        queue="agent_plan",
    )
