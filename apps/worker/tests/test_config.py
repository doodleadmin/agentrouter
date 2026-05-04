"""Tests for worker settings."""

from app.config import Settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.CELERY_BROKER_URL.startswith("redis://")
    assert s.TASK_MAX_RETRIES == 3
    assert s.TASK_RETRY_BACKOFF is True
    assert s.WORKER_CONCURRENCY == 4
    assert s.API_BASE_URL.startswith("http")
    assert s.API_TIMEOUT_SECONDS == 420.0  # BE-10 P2-6: 420 s >= session timeout (300) + buffer


def test_api_timeout_default_is_420() -> None:
    """BE-10 P2-6: Worker API timeout must be >= API RUNTIME_SESSION_TIMEOUT (300)
    + buffer for HTTP overhead and real OpenCode plans (80–170 s actual).
    420 s provides safe headroom for one full session timeout plus response."""
    s = Settings()
    assert s.API_TIMEOUT_SECONDS == 420.0
    assert isinstance(s.API_TIMEOUT_SECONDS, (int, float))


def test_be10_worker_timout_default_420() -> None:
    """P2-6: Confirm worker API_TIMEOUT_SECONDS == 420.0."""
    s = Settings()
    assert s.API_TIMEOUT_SECONDS == 420.0
