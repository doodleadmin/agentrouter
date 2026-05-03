from types import SimpleNamespace

from app.handlers import bind_topic, topic_status, unbind_topic


class FakeApiClient:
    def __init__(self):
        self._topic = None

    async def find_project_by_slug(self, slug: str):
        if slug == "academy-bot":
            return {"id": "p-1", "slug": slug}
        return None

    async def find_agent_by_slug(self, slug: str):
        if slug == "backend":
            return {"id": "a-1", "slug": slug}
        return None

    async def find_topic_binding(self, chat_id: int, message_thread_id: int | None):
        return self._topic

    async def create_topic_binding(self, **kwargs):
        self._topic = {
            "id": "t-1",
            "chat_id": kwargs["chat_id"],
            "message_thread_id": kwargs["message_thread_id"],
            "project_id": kwargs["project_id"],
            "agent_id": kwargs["agent_id"],
            "is_active": True,
        }
        return self._topic

    async def update_topic_binding(self, topic_id: str, **kwargs):
        assert topic_id == "t-1"
        self._topic.update(
            {
                "project_id": kwargs["project_id"],
                "agent_id": kwargs["agent_id"],
                "is_active": kwargs.get("is_active", True),
            }
        )
        return self._topic

    async def deactivate_topic_binding(self, topic_id: str):
        assert topic_id == "t-1"
        self._topic["is_active"] = False
        return self._topic


class FakeMessage:
    def __init__(self, text: str, thread_id: int | None = 7):
        self.text = text
        self.message_thread_id = thread_id
        self.chat = SimpleNamespace(id=100)
        self.answers = []

    async def answer(self, text: str, message_thread_id: int | None = None):
        self.answers.append((text, message_thread_id))


async def test_bind_topic_success(monkeypatch) -> None:
    client = FakeApiClient()
    msg = FakeMessage("/bind_topic project=academy-bot agent=backend", thread_id=7)
    monkeypatch.setattr(bind_topic, "get_api_client", lambda: client)

    await bind_topic.bind_topic_handler(msg)

    assert client._topic is not None
    assert "Привязка topic" in msg.answers[0][0]


async def test_bind_topic_forum_only(monkeypatch) -> None:
    client = FakeApiClient()
    msg = FakeMessage("/bind_topic project=academy-bot agent=backend", thread_id=None)
    monkeypatch.setattr(bind_topic, "get_api_client", lambda: client)

    await bind_topic.bind_topic_handler(msg)

    assert "только внутри forum topic" in msg.answers[0][0]


async def test_unbind_topic_success(monkeypatch) -> None:
    client = FakeApiClient()
    client._topic = {
        "id": "t-1",
        "chat_id": 100,
        "message_thread_id": 7,
        "project_id": "p-1",
        "agent_id": "a-1",
        "is_active": True,
    }
    msg = FakeMessage("/unbind_topic", thread_id=7)
    monkeypatch.setattr(unbind_topic, "get_api_client", lambda: client)

    await unbind_topic.unbind_topic_handler(msg)

    assert client._topic["is_active"] is False
    assert "soft deactivate" in msg.answers[0][0]


async def test_topic_status_bound(monkeypatch) -> None:
    client = FakeApiClient()
    client._topic = {
        "id": "t-1",
        "chat_id": 100,
        "message_thread_id": 7,
        "project_id": "p-1",
        "agent_id": "a-1",
        "is_active": True,
    }
    msg = FakeMessage("/topic_status", thread_id=7)
    monkeypatch.setattr(topic_status, "get_api_client", lambda: client)

    await topic_status.topic_status_handler(msg)

    assert "Topic status" in msg.answers[0][0]
    assert "status=active" in msg.answers[0][0]
