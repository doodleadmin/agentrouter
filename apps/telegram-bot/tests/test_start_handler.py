from types import SimpleNamespace

from app.handlers import start


class FakeMessage:
    def __init__(self, chat_type: str = "private"):
        self.chat = SimpleNamespace(type=chat_type)
        self.answers = []

    async def answer(self, text: str, **kwargs):
        self.answers.append({"text": text, "kwargs": kwargs})


async def test_start_private_with_webapp_button(monkeypatch) -> None:
    msg = FakeMessage(chat_type="private")
    monkeypatch.setattr(start.settings, "TELEGRAM_WEBAPP_URL", "https://example.com/webapp")

    await start.start_handler(msg)

    assert len(msg.answers) == 1
    payload = msg.answers[0]
    assert "Agent Mission Control Bot" in payload["text"]
    markup = payload["kwargs"].get("reply_markup")
    assert markup is not None
    button = markup.inline_keyboard[0][0]
    assert button.text == "Открыть AI Office"
    assert button.web_app.url == "https://example.com/webapp"


async def test_start_without_webapp_url_fallback(monkeypatch) -> None:
    msg = FakeMessage(chat_type="private")
    monkeypatch.setattr(start.settings, "TELEGRAM_WEBAPP_URL", "")

    await start.start_handler(msg)

    assert len(msg.answers) == 1
    assert "Agent Mission Control Bot" in msg.answers[0]["text"]
    assert msg.answers[0]["kwargs"].get("reply_markup") is None


async def test_start_non_private_no_button(monkeypatch) -> None:
    msg = FakeMessage(chat_type="group")
    monkeypatch.setattr(start.settings, "TELEGRAM_WEBAPP_URL", "https://example.com/webapp")

    await start.start_handler(msg)

    assert len(msg.answers) == 1
    assert msg.answers[0]["kwargs"].get("reply_markup") is None
