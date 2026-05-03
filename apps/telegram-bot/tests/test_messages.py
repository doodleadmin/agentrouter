from types import SimpleNamespace

from app.handlers import messages
from app.services.topic_context import TopicContext


class FakeApiClient:
    def __init__(self, *, trigger_plan_fails: bool = False):
        self.created_payload = None
        self.triggered_plan_task_id: str | None = None
        self._trigger_plan_fails = trigger_plan_fails

    async def create_task(self, payload):
        self.created_payload = payload
        return {"external_id": "task-0001", "id": "00000000-0000-0000-0000-000000000099"}

    async def trigger_plan(self, task_id: str):
        if self._trigger_plan_fails:
            raise RuntimeError("backend unavailable")
        self.triggered_plan_task_id = task_id


class FakeMessage:
    def __init__(self, text: str, chat_id: int = 100, thread_id: int | None = 10, username: str = "tester"):
        self.text = text
        self.chat = SimpleNamespace(id=chat_id)
        self.message_thread_id = thread_id
        self.from_user = SimpleNamespace(id=77, username=username)
        self.answers = []

    async def answer(self, text: str, message_thread_id: int | None = None):
        self.answers.append((text, message_thread_id))


def test_make_title_truncates() -> None:
    long_text = "x" * 200
    title = messages._make_title(long_text)
    assert len(title) == 120


async def test_text_message_unbound_topic(monkeypatch) -> None:
    msg = FakeMessage("hello")

    async def _resolve(*args, **kwargs):
        return TopicContext(is_bound=False)

    monkeypatch.setattr(messages, "resolve_topic_context", _resolve)
    monkeypatch.setattr(messages, "get_api_client", lambda: FakeApiClient())

    await messages.text_message_handler(msg)

    assert len(msg.answers) == 1
    assert "не привязан" in msg.answers[0][0]
    assert "/bind_topic project=<project_slug> agent=<agent_slug>" in msg.answers[0][0]
    assert msg.answers[0][1] == 10


async def test_text_message_bound_topic_creates_task_and_triggers_plan(monkeypatch) -> None:
    msg = FakeMessage("implement endpoint")
    fake_client = FakeApiClient()

    async def _resolve(*args, **kwargs):
        return TopicContext(
            is_bound=True,
            kind="project",
            project_id="00000000-0000-0000-0000-000000000001",
            agent_id="00000000-0000-0000-0000-000000000002",
            title="Project: demo",
        )

    monkeypatch.setattr(messages, "resolve_topic_context", _resolve)
    monkeypatch.setattr(messages, "get_api_client", lambda: fake_client)

    await messages.text_message_handler(msg)

    assert fake_client.created_payload is not None
    assert fake_client.created_payload["telegram_chat_id"] == 100
    assert fake_client.created_payload["telegram_thread_id"] == 10
    assert fake_client.triggered_plan_task_id == "00000000-0000-0000-0000-000000000099"
    assert len(msg.answers) == 1
    assert "Task создан" in msg.answers[0][0]
    assert "Plan pipeline запущен" in msg.answers[0][0]


async def test_text_message_bound_topic_plan_trigger_fails_gracefully(monkeypatch) -> None:
    msg = FakeMessage("implement endpoint")
    fake_client = FakeApiClient(trigger_plan_fails=True)

    async def _resolve(*args, **kwargs):
        return TopicContext(
            is_bound=True,
            kind="project",
            project_id="00000000-0000-0000-0000-000000000001",
            agent_id="00000000-0000-0000-0000-000000000002",
            title="Project: demo",
        )

    monkeypatch.setattr(messages, "resolve_topic_context", _resolve)
    monkeypatch.setattr(messages, "get_api_client", lambda: fake_client)

    await messages.text_message_handler(msg)

    assert fake_client.created_payload is not None
    assert fake_client.triggered_plan_task_id is None
    assert len(msg.answers) == 1
    assert "Task создан" in msg.answers[0][0]
    assert "не удалось запустить" in msg.answers[0][0]
