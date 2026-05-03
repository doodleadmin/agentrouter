"""Telegram bot configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Telegram bot app."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    TELEGRAM_BOT_TOKEN: str = ""
    API_BASE_URL: str = "http://localhost:8000"
    API_TIMEOUT_SECONDS: float = 10.0
    POLLING_ALLOWED_UPDATES: list[str] = []


settings = Settings()
