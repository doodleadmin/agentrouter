"""
Application configuration via environment variables.

Uses pydantic-settings for type-safe settings management.
All sensitive values come from .env (never hardcoded).
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "Agent Mission Control API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    COMMIT_SHA: str = "unknown"  # injected at build time
    BUILD_TIME: str = "unknown"  # injected at build time

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://agent_mc:agent_mc@localhost:5432/agent_mc"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""  # set in .env
    TELEGRAM_WEBHOOK_URL: str = ""  # set in .env (production only)

    # OpenAI / Embedding
    OPENAI_API_KEY: str = ""  # set in .env (optional)
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Memory Vault
    MEMORY_VAULT_PATH: str = ".ai_memory"

    # Git
    REPOS_PATH: str = "/opt/mc/repos"
    WORKTREES_PATH: str = "/opt/mc/worktrees"

    # Runtime provider (BE-04 / BE-05)
    RUNTIME_PROVIDER: str = "stub"  # stub | opencode_http
    OPENCODE_SERVER_URL: str = ""  # required for opencode_http
    RUNTIME_ALLOW_REAL_OPENCODE_HTTP: bool = False  # BE-05 M-3: explicit gate for real transport
    RUNTIME_ALLOWED_ROOT: str = "."
    RUNTIME_MEMORY_TOP_K: int = 5
    # BE-10 P2-6: 300 s provides safe headroom for real OpenCode plans
    # (80–170 s actual observed in BE-08 smoke test). Must be less than
    # worker's API_TIMEOUT_SECONDS (420) to allow worker to surface the
    # timeout as a controlled error rather than a connection drop.
    RUNTIME_SESSION_TIMEOUT_SECONDS: int = 300
    RUNTIME_IDLE_TIMEOUT_SECONDS: int = 20
    RUNTIME_MAX_RETRIES: int = 2
    RUNTIME_MAX_PLAN_BYTES: int = 100_000  # 100 KB hard cap for plan text


settings = Settings()
