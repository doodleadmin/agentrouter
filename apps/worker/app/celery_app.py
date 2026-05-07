"""Celery application factory and configuration.

Creates a Celery app with:
- Explicitly declared queues
- JSON serializer for task args/results
- Retry/backoff defaults from settings
- Route decorators per task module
"""

import os
import signal
import sys

import celery.apps.worker as _worker_module
from celery import Celery
from celery.platforms import close_open_fds
from celery.signals import worker_ready

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


# WORKER-LINUX-01: Fix Celery's broken SIGHUP restart mechanism.
#
# Root cause: Celery's install_worker_restart_handler() registers a SIGHUP handler
# (when stdout is not a TTY, i.e. nohup) that calls _reload_current_worker():
#   os.execv(sys.executable, [sys.executable] + sys.argv)
# When started via `python -m celery ...`, sys.argv[0] is the full path to
# celery/__main__.py. The os.execv restart runs it as a standalone script
# (not via -m), so `from . import maybe_patch_concurrency` fails with:
#   "ImportError: attempted relative import with no known parent package"
#
# Fix: monkey-patch _reload_current_worker to use `-m celery` instead.
# Also override the SIGHUP handler to SIG_IGN as defense in depth.


def _fixed_reload_current_worker():
    """Fixed restart: uses `python -m celery` to preserve package context."""
    close_open_fds([sys.__stdin__, sys.__stdout__, sys.__stderr__])
    # Use -m celery so relative imports in celery/__main__.py work correctly
    os.execv(sys.executable, [sys.executable, '-m', 'celery'] + sys.argv[1:])


# Monkey-patch the broken function
_worker_module._reload_current_worker = _fixed_reload_current_worker


@worker_ready.connect
def _reset_sighup_after_celery_init(**kwargs):
    """Override Celery's SIGHUP restart handler to SIG_IGN.

    Defense in depth: even with the fixed _reload_current_worker, we don't
    want SIGHUP restarts in dev — they serve no purpose for solo pool.
    """
    try:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
    except (OSError, ValueError):
        pass  # SIGHUP not available on this platform (e.g. Windows)
