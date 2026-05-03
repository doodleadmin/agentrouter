"""Celery application factory and configuration.

Creates a Celery app with:
- Explicitly declared queues
- JSON serializer for task args/results
- Retry/backoff defaults from settings
- Route decorators per task module
"""

from celery import Celery

from app.config import settings
from app.queues import ALL_QUEUES


def create_celery_app() -> Celery:
    """Create and configure the Celery application instance."""

    app = Celery("agent_mc_worker")

    app.conf.update(
        # Broker / result backend
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,

        # Serialization
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],

        # Queues — declare all queues explicitly
        task_queues={
            q: {"exchange": q, "routing_key": q} for q in ALL_QUEUES
        },
        task_default_queue="telegram_inbound",

        # Retry defaults
        task_acks_late=True,
        task_reject_on_worker_lost=True,

        # Worker
        worker_concurrency=settings.WORKER_CONCURRENCY,
        worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",

        # Result expiry
        result_expires=3600,
    )

    # Auto-discover task modules
    app.autodiscover_tasks(
        [
            "app.tasks.health",
            "app.tasks.telegram_inbound",
            "app.tasks.agent_plan",
            "app.tasks.agent_execute",
            "app.tasks.memory_index",
            "app.tasks.deploy",
            "app.tasks.notifications",
        ],
    )

    return app


# Module-level app instance (used by `celery -A app.celery_app worker`)
celery_app = create_celery_app()
