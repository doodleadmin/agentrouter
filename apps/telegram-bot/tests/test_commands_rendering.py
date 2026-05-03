from app.handlers import commands


class FakeApiClient:
    async def list_projects(self):
        return [{"slug": "academy-bot", "name": "Academy Bot"}]

    async def list_agents(self):
        return [{"slug": "backend", "role": "backend-architect"}]

    async def list_tasks(self, limit: int = 20):
        return [{"external_id": "task-0001", "status": "created", "title": "test task"}]


class FakeMessage:
    def __init__(self):
        self.message_thread_id = 99
        self.answers = []

    async def answer(self, text: str, message_thread_id: int | None = None):
        self.answers.append((text, message_thread_id))


async def test_projects_command(monkeypatch) -> None:
    msg = FakeMessage()
    monkeypatch.setattr(commands, "get_api_client", lambda: FakeApiClient())
    await commands.projects_handler(msg)
    assert "Активные проекты" in msg.answers[0][0]
    assert msg.answers[0][1] == 99


async def test_agents_command(monkeypatch) -> None:
    msg = FakeMessage()
    monkeypatch.setattr(commands, "get_api_client", lambda: FakeApiClient())
    await commands.agents_handler(msg)
    assert "Активные агенты" in msg.answers[0][0]


async def test_tasks_command(monkeypatch) -> None:
    msg = FakeMessage()
    monkeypatch.setattr(commands, "get_api_client", lambda: FakeApiClient())
    await commands.tasks_handler(msg)
    assert "Последние задачи" in msg.answers[0][0]
