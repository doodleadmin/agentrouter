"""Telegram WebApp initData validation utility.

Validates Telegram WebApp signatures using TELEGRAM_BOT_TOKEN without exposing
the token or trusting client-side checks.

TODO: Add replay protection by enforcing max age on auth_date and one-time
nonce storage (e.g., Redis) for high-sensitivity actions.
Recommended safe baseline: reject initData older than 60 seconds and store
hash as single-use token for a short TTL.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl


class TelegramWebAppAuthError(ValueError):
    """Raised when Telegram WebApp auth data is invalid."""


def validate_telegram_webapp_init_data(init_data: str, bot_token: str) -> dict:
    """Return verified minimal user payload from Telegram WebApp initData."""
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

    raw_user = pairs.get("user")
    if not raw_user:
        raise TelegramWebAppAuthError("initData user payload is missing")
    try:
        user = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise TelegramWebAppAuthError("initData user payload is malformed") from exc

    auth_date = pairs.get("auth_date")
    if auth_date is None:
        raise TelegramWebAppAuthError("initData auth_date is missing")

    try:
        user_id = int(user["id"])
        auth_date_int = int(auth_date)
    except (KeyError, TypeError, ValueError) as exc:
        raise TelegramWebAppAuthError("initData required fields are invalid") from exc

    return {
        "user_id": user_id,
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "username": user.get("username"),
        "auth_date": auth_date_int,
        "hash_summary": f"{incoming_hash[:8]}...{incoming_hash[-8:]}",
    }
