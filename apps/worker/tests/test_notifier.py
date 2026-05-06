"""Tests for notifier adapter."""

from unittest.mock import MagicMock, patch

from app.services.notifier import (
    StubNotifier,
    TelegramNotifier,
    get_notifier,
    set_notifier,
)


def test_stub_notifier_records_calls() -> None:
    notifier = StubNotifier()
    notifier.send(chat_id=100, thread_id=5, text="hello")
    notifier.send(chat_id=200, thread_id=None, text="world")

    assert len(notifier.sent) == 2
    assert notifier.sent[0] == {"chat_id": 100, "thread_id": 5, "text": "hello"}
    assert notifier.sent[1] == {"chat_id": 200, "thread_id": None, "text": "world"}


def test_stub_notifier_returns_ok() -> None:
    notifier = StubNotifier()
    result = notifier.send(chat_id=1, thread_id=None, text="test")
    assert result["ok"] is True
    assert result["method"] == "stub"


def test_telegram_notifier_init() -> None:
    """TelegramNotifier should build correct API URL."""
    notifier = TelegramNotifier("123456:ABC")
    assert "123456:ABC" in notifier._api_url
    assert notifier._api_url.startswith("https://api.telegram.org/bot")


# ── TG-05: get_notifier factory tests ──────────────────────────────────


def test_get_notifier_returns_stub_when_token_empty(monkeypatch) -> None:
    """get_notifier returns StubNotifier when TELEGRAM_BOT_TOKEN is empty."""
    set_notifier(None)  # reset singleton
    mock_settings = MagicMock()
    mock_settings.TELEGRAM_BOT_TOKEN = ""
    with patch("app.services.notifier.settings", mock_settings, create=True):
        # Patch the import inside get_notifier
        with patch.dict("sys.modules", {"app.config": MagicMock(settings=mock_settings)}):
            notifier = get_notifier()
            assert isinstance(notifier, StubNotifier)
    set_notifier(None)  # cleanup


def test_get_notifier_returns_telegram_when_token_set(monkeypatch) -> None:
    """get_notifier returns TelegramNotifier when TELEGRAM_BOT_TOKEN is set."""
    set_notifier(None)  # reset singleton
    mock_settings = MagicMock()
    mock_settings.TELEGRAM_BOT_TOKEN = "test-token-123"
    with patch.dict("sys.modules", {"app.config": MagicMock(settings=mock_settings)}):
        notifier = get_notifier()
        assert isinstance(notifier, TelegramNotifier)
    set_notifier(None)  # cleanup


def test_telegram_notifier_send_success() -> None:
    """TelegramNotifier.send returns Telegram API response on success."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"ok": True, "method": "sendMessage", "result": {"message_id": 42}}

    with patch("app.services.notifier.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        notifier = TelegramNotifier("test-token-123")
        result = notifier.send(chat_id=100, thread_id=5, text="hello")

        assert result["ok"] is True
        assert result["method"] == "sendMessage"
        # Verify correct URL was called
        call_args = mock_client.post.call_args
        assert "sendMessage" in call_args[0][0]
        assert call_args[1]["json"]["chat_id"] == 100
        assert call_args[1]["json"]["text"] == "hello"


def test_telegram_notifier_send_failure_does_not_leak_token() -> None:
    """TelegramNotifier.send failure must not expose the token in exception."""
    with patch("app.services.notifier.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("connection timeout")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        notifier = TelegramNotifier("super-secret-token-do-not-leak")
        try:
            notifier.send(chat_id=100, thread_id=None, text="test")
        except Exception as exc:
            # Token must NOT appear in the exception message
            assert "super-secret-token-do-not-leak" not in str(exc)
            assert "super-secret-token-do-not-leak" not in repr(exc)
        else:
            # If no exception raised, that's also fine (httpx.Client context manager)
            pass


def test_set_notifier_override() -> None:
    """set_notifier allows overriding the singleton for testing."""
    custom = StubNotifier()
    set_notifier(custom)
    assert get_notifier() is custom
    set_notifier(None)  # cleanup
