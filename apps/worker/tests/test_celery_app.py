"""Tests for Celery app configuration and queue setup."""

from app.celery_app import celery_app
from app.queues import ALL_QUEUES


def test_all_queues_declared() -> None:
    """All 7 named queues should be declared in Celery config."""
    declared = set(celery_app.conf.task_queues.keys())
    expected = set(ALL_QUEUES)
    assert expected == declared
    assert len(declared) == 7


def test_default_queue_is_telegram_inbound() -> None:
    """Default queue should be telegram_inbound."""
    assert celery_app.conf.task_default_queue == "telegram_inbound"


def test_json_serializer() -> None:
    """Celery should use JSON serialization."""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert "json" in celery_app.conf.accept_content


def test_acks_late() -> None:
    """Tasks should ack late for reliability."""
    assert celery_app.conf.task_acks_late is True


def test_result_expires() -> None:
    """Results should expire after 1 hour."""
    assert celery_app.conf.result_expires == 3600
