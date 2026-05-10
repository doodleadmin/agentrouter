"""Telegram bot configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Telegram bot app."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_USER_IDS: str = ""  # comma-separated Telegram user IDs; empty = fail-closed
    API_BASE_URL: str = "http://localhost:8000"
    API_TIMEOUT_SECONDS: float = 10.0
    TELEGRAM_WEBAPP_URL: str = ""
    POLLING_ALLOWED_UPDATES: list[str] = []
    CALLBACK_SECRET: str = ""  # HMAC signing secret for callback_data (shared with API)

    def admin_user_ids(self) -> list[int]:
        """Return parsed admin user ID list. Empty string = empty list (fail-closed)."""
        raw = self.TELEGRAM_ADMIN_USER_IDS
        if not raw or raw.strip() == "":
            return []
        try:
            return [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            return []


settings = Settings()
