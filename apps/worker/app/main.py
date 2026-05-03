"""Entrypoint for Celery worker.

Usage (after separate approve):

    celery -A app.celery_app worker \
        --loglevel=info \
        --queues=telegram_inbound,agent_plan,agent_execute \
        --concurrency=4

For dev polling of all queues:

    celery -A app.celery_app worker --loglevel=info

This module does NOT start the worker automatically.
It only exposes the celery_app for the CLI runner.
"""

from app.celery_app import celery_app  # noqa: F401

__all__ = ["celery_app"]
