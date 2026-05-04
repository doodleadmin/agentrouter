"""Worker configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Celery worker."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Task retry policy
    TASK_MAX_RETRIES: int = 3
    TASK_RETRY_BACKOFF: bool = True
    TASK_RETRY_BACKOFF_MAX: int = 600  # seconds
    TASK_RETRY_JITTER: bool = True

    # Backend API (for tasks that need to call orchestrator)
    API_BASE_URL: str = "http://localhost:8000"
    # BE-10 P2-6: Must be >= API RUNTIME_SESSION_TIMEOUT_SECONDS (300) + buffer
    # for HTTP overhead, retries, and real OpenCode plans (80–170 s actual).
    # 420 s provides safe headroom for one full session timeout plus response.
    API_TIMEOUT_SECONDS: float = 420.0

    # Telegram Bot (for notifications sent from worker)
    TELEGRAM_BOT_TOKEN: str = ""

    # Worker
    WORKER_CONCURRENCY: int = 4
    WORKER_LOG_LEVEL: str = "INFO"

    # Sandbox runner mode (WRK-04)
    SANDBOX_RUNNER_MODE: str = "fake"  # fake|docker

    # Manual test mode (WRK-04-hardening) — enables manual-test-* worktree prefix
    # ONLY for controlled local smoke tests. MUST be False in production.
    SANDBOX_MANUAL_TEST_MODE: bool = False

    # Docker sandbox (opt-in only)
    DOCKER_SANDBOX_IMAGE: str = "amc-agent-sandbox:dev"
    DOCKER_SANDBOX_TIMEOUT_SECONDS: int = 120
    DOCKER_SANDBOX_MEMORY_LIMIT: str = "2g"
    DOCKER_SANDBOX_CPU_LIMIT: float = 2.0
    DOCKER_SANDBOX_PIDS_LIMIT: int = 256
    DOCKER_SANDBOX_NETWORK_MODE: str = "none"  # keep no external network by default


settings = Settings()
