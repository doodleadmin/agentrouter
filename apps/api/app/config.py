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


settings = Settings()
