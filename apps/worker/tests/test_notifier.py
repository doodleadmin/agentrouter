"""Tests for notifier adapter."""

from app.services.notifier import StubNotifier, TelegramNotifier


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
