"""Tests for worker settings."""

from app.config import Settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.CELERY_BROKER_URL.startswith("redis://")
    assert s.TASK_MAX_RETRIES == 3
    assert s.TASK_RETRY_BACKOFF is True
    assert s.WORKER_CONCURRENCY == 4
    assert s.API_BASE_URL.startswith("http")
    assert s.API_TIMEOUT_SECONDS == 300.0  # BE-09: must cover real OpenCode plans


def test_api_timeout_default_is_300() -> None:
    """BE-09: Worker API timeout must be >= API RUNTIME_SESSION_TIMEOUT (180)
    + buffer for real OpenCode plans (80–170 s actual)."""
    s = Settings()
    assert s.API_TIMEOUT_SECONDS == 300.0
    assert isinstance(s.API_TIMEOUT_SECONDS, (int, float))
