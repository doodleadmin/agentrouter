"""Schemas for Telegram WebApp auth verification endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class TelegramWebAppAuthRequest(BaseModel):
    """Incoming Telegram WebApp initData payload."""

    initData: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class TelegramWebAppAuthResponse(BaseModel):
    """Minimal verified Telegram WebApp user payload."""

    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    auth_date: int
    hash_summary: str
    session_token: str
