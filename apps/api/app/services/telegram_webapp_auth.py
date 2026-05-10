"""Telegram WebApp initData validation utility.

Validates Telegram WebApp signatures using TELEGRAM_BOT_TOKEN without exposing
the token or trusting client-side checks.

Security measures:
- HMAC-SHA256 signature verification against bot token
- auth_date freshness check (configurable max age, default 300 s)
- Session token derivation from verified hash for replay-protection foundation
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


# Default max age for initData in seconds (5 minutes — Telegram recommendation).
WEBAPP_AUTH_MAX_AGE_SECONDS: int = 300


class TelegramWebAppAuthError(ValueError):
    """Raised when Telegram WebApp auth data is invalid."""


def _derive_session_token(incoming_hash: str, bot_token: str) -> str:
    """Derive a short-lived session token from verified hash + bot token.

    This is NOT a substitute for proper session management — it provides
    a deterministic, non-reversible binding that can be used as a session
    identifier or stored as a one-time-use token with TTL in Redis.
    """
    return hashlib.sha256(
        f"webapp_session:{incoming_hash}:{bot_token}".encode("utf-8")
    ).hexdigest()[:32]


def validate_telegram_webapp_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = WEBAPP_AUTH_MAX_AGE_SECONDS,
    _now: float | None = None,
) -> dict:
    """Return verified minimal user payload from Telegram WebApp initData.

    Parameters
    ----------
    init_data:
        Raw initData query string from ``Telegram.WebApp.initData``.
    bot_token:
        Telegram bot token used for HMAC key derivation.
    max_age_seconds:
        Maximum allowed age of ``auth_date`` in seconds. Default 300 (5 min).
    _now:
        Override current time for deterministic testing. Defaults to ``time.time()``.
    """
    if not bot_token:
        raise TelegramWebAppAuthError("Telegram bot token is not configured")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    incoming_hash = pairs.get("hash")
    if not incoming_hash:
        raise TelegramWebAppAuthError("initData hash is missing")

    data_check_string = "\n".join(
        sorted(f"{k}={v}" for k, v in pairs.items() if k != "hash")
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, incoming_hash):
        raise TelegramWebAppAuthError("initData signature is invalid")

    # ── auth_date freshness ────────────────────────────────────────────
    auth_date = pairs.get("auth_date")
    if auth_date is None:
        raise TelegramWebAppAuthError("initData auth_date is missing")

    try:
        auth_date_int = int(auth_date)
    except (TypeError, ValueError) as exc:
        raise TelegramWebAppAuthError("initData auth_date is malformed") from exc

    now = _now if _now is not None else time.time()
    age = now - auth_date_int
    if age < 0:
        raise TelegramWebAppAuthError("initData auth_date is in the future")
    if age > max_age_seconds:
        raise TelegramWebAppAuthError(
            f"initData auth_date is too old ({age:.0f}s > {max_age_seconds}s max age)"
        )

    # ── user payload extraction ────────────────────────────────────────
    raw_user = pairs.get("user")
    if not raw_user:
        raise TelegramWebAppAuthError("initData user payload is missing")
    try:
        user = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise TelegramWebAppAuthError("initData user payload is malformed") from exc

    try:
        user_id = int(user["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TelegramWebAppAuthError("initData required fields are invalid") from exc

    # ── session token (replay protection foundation) ───────────────────
    session_token = _derive_session_token(incoming_hash, bot_token)

    return {
        "user_id": user_id,
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "username": user.get("username"),
        "auth_date": auth_date_int,
        "hash_summary": f"{incoming_hash[:8]}...{incoming_hash[-8:]}",
        "session_token": session_token,
    }
