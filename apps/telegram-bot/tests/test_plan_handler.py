"""TG-03: Tests for /plan handler."""

from app.handlers import plan_handler as mod


class FakeApiClient:
    def __init__(self, *, task_return=None, plan_return=None, get_task_fails: bool = False):
        self._task = task_return  # None = not found
        self._plan = plan_return or {}
        self._get_task_fails = get_task_fails
        self._get_task_calls = []
        self._find_calls = []
        self._plan_calls = []

    async def get_task(self, task_id: str):
        self._get_task_calls.append(task_id)
        if self._task is None or self._get_task_fails:
            import httpx
            from httpx import HTTPStatusError
            raise HTTPStatusError("not found", request=httpx.Request("GET", "/"), response=httpx.Response(404))
        return self._task

    async def find_task_by_external_id(self, external_id: str):
        self._find_calls.append(external_id)
        return self._task

    async def get_task_plan(self, task_id: str):
        self._plan_calls.append(task_id)
        return self._plan


class FakeMessage:
    def __init__(self):
        self.message_thread_id = 99
        self.from_user = FakeUser()
        self.text = ""
        self.answers = []

    async def answer(self, text: str, reply_markup=None, parse_mode=None, **kwargs):
        self.answers.append({"text": text, "reply_markup": reply_markup})


class FakeUser:
    id = 12345


async def test_plan_no_args(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/plan"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient())
    await mod.plan_handler(msg)
    assert "Usage" in msg.answers[0]["text"]


async def test_plan_task_not_found(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/plan task-9999"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(task_return=None))
    await mod.plan_handler(msg)
    assert "not found" in msg.answers[0]["text"].lower()


async def test_plan_empty(monkeypatch) -> None:
    task = {"id": "uuid-123", "external_id": "task-0001"}
    plan = {"task_id": "uuid-123", "plan_text": None, "plan_version": 1, "status": "created"}
    msg = FakeMessage()
    msg.text = "/plan uuid-123"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(task_return=task, plan_return=plan))
    await mod.plan_handler(msg)
    assert "Plan" in msg.answers[0]["text"]
    assert "created" in msg.answers[0]["text"]


async def test_plan_with_content(monkeypatch) -> None:
    task = {"id": "uuid-123", "external_id": "task-0002"}
    plan = {
        "task_id": "uuid-123",
        "plan_text": "Step 1: Setup\nStep 2: Implement\nStep 3: Test",
        "plan_version": 1,
        "status": "approved",
    }
    msg = FakeMessage()
    msg.text = "/plan uuid-123"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(task_return=task, plan_return=plan))
    await mod.plan_handler(msg)
    text = msg.answers[0]["text"]
    assert "Step 1" in text
    assert "Step 2" in text
    assert "Step 3" in text
    assert msg.answers[0]["reply_markup"] is not None  # plan keyboard
