"""Tests for worker settings."""

from app.config import Settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.CELERY_BROKER_URL.startswith("redis://")
    assert s.TASK_MAX_RETRIES == 3
    assert s.TASK_RETRY_BACKOFF is True
    assert s.WORKER_CONCURRENCY == 4
    assert s.API_BASE_URL.startswith("http")
