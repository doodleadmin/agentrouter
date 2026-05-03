"""Notification adapter for sending messages to Telegram topics.

Provides:
- ``Notifier`` protocol (sync interface for Celery tasks)
- ``TelegramNotifier`` — real Telegram Bot API via httpx
- ``StubNotifier`` — records calls, for testing
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    """Sync protocol — Celery tasks are synchronous."""

    def send(self, chat_id: int, thread_id: int | None, text: str) -> dict: ...


class TelegramNotifier:
    """Send messages to Telegram topics via Bot API."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._api_url = f"https://api.telegram.org/bot{token}"

    def send(self, chat_id: int, thread_id: int | None, text: str) -> dict:
        payload: dict = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if thread_id is not None:
            payload["message_thread_id"] = thread_id

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self._api_url}/sendMessage", json=payload)
            resp.raise_for_status()
            return resp.json()


class StubNotifier:
    """Records notification calls instead of sending them. Used for testing."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, chat_id: int, thread_id: int | None, text: str) -> dict:
        self.sent.append({
            "chat_id": chat_id,
            "thread_id": thread_id,
            "text": text,
        })
        return {"ok": True, "method": "stub"}


_notifier: Notifier | None = None


def get_notifier() -> Notifier:
    """Factory: returns TelegramNotifier if token is set, else StubNotifier."""
    global _notifier
    if _notifier is None:
        from app.config import settings

        if settings.TELEGRAM_BOT_TOKEN:
            _notifier = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN)
        else:
            logger.warning("TELEGRAM_BOT_TOKEN not set — using StubNotifier")
            _notifier = StubNotifier()
    return _notifier


def set_notifier(notifier: Notifier) -> None:
    """Override notifier for testing."""
    global _notifier
    _notifier = notifier
