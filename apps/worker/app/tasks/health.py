"""Healthcheck task — verifies Celery broker connectivity."""

from app.celery_app import celery_app
from app.config import settings
from app.queues import TELEGRAM_INBOUND


@celery_app.task(
    name="tasks.healthcheck",
    queue=TELEGRAM_INBOUND,
    max_retries=0,
)
def healthcheck() -> dict[str, str]:
    """Simple healthcheck: returns ok if broker is reachable."""
    return {
        "status": "ok",
        "broker": settings.CELERY_BROKER_URL,
        "worker_concurrency": str(settings.WORKER_CONCURRENCY),
    }
