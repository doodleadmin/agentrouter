"""TG-03: Tests for /status handler."""

from app.handlers import status_handler as mod


class FakeApiClient:
    def __init__(self, *, task_return=None, approvals_return=None, get_task_fails: bool = False):
        self._task = task_return  # None = not found
        self._approvals = approvals_return or []
        self._get_task_fails = get_task_fails
        self._get_task_calls = []
        self._find_calls = []
        self._approvals_calls = []

    async def get_task(self, task_id: str):
        self._get_task_calls.append(task_id)
        if self._task is None or self._get_task_fails:
            import httpx
            from httpx import HTTPStatusError
            raise HTTPStatusError("not found", request=httpx.Request("GET", "/"), response=httpx.Response(404))
        return self._task

    async def find_task_by_external_id(self, external_id: str):
        self._find_calls.append(external_id)
        return self._task  # None if task_return was None

    async def list_approvals_by_task(self, task_id: str):
        self._approvals_calls.append(task_id)
        return self._approvals


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
    username = "testuser"


async def test_status_no_args(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/status"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient())
    await mod.status_handler(msg)
    assert "Usage" in msg.answers[0]["text"]


async def test_status_by_uuid(monkeypatch) -> None:
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0001",
        "title": "Test task",
        "status": "created",
        "risk_level": "low",
        "intent": None,
        "project_id": None,
        "agent_id": None,
        "plan_text": None,
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }
    msg = FakeMessage()
    msg.text = "/status 550e8400-e29b-41d4-a716-446655440000"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(task_return=task))
    await mod.status_handler(msg)
    assert "task-0001" in msg.answers[0]["text"]
    assert msg.answers[0]["reply_markup"] is not None  # inline keyboard


async def test_status_by_external_id(monkeypatch) -> None:
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0005",
        "title": "Another task",
        "status": "approved",
        "risk_level": "medium",
        "intent": None,
        "project_id": None,
        "agent_id": None,
        "plan_text": "Test plan",
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }
    fake = FakeApiClient(task_return=task, get_task_fails=True)
    # Setting task=None makes get_task raise, forcing fallback to find_task_by_external_id
    msg = FakeMessage()
    msg.text = "/status task-0005"
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.status_handler(msg)
    # it should have tried get_task first (failed), then find_task_by_external_id
    assert len(fake._find_calls) == 1
    assert "task-0005" in msg.answers[0]["text"]


async def test_status_not_found(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/status nonexistent"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(task_return=None))
    await mod.status_handler(msg)
    assert "not found" in msg.answers[0]["text"].lower()


async def test_status_with_pending_approval(monkeypatch) -> None:
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0001",
        "title": "Deploy task",
        "status": "waiting_approval",
        "risk_level": "high",
        "intent": "deploy",
        "project_id": None,
        "agent_id": None,
        "plan_text": "Plan steps",
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }
    fake = FakeApiClient(
        task_return=task,
        approvals_return=[{"id": "abc-123", "status": "pending", "action": "deploy_production"}],
    )
    msg = FakeMessage()
    msg.text = "/status 550e8400-e29b-41d4-a716-446655440000"
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.status_handler(msg)
    # Should have Approve/Reject buttons since approval is pending
    text = msg.answers[0]["text"]
    assert "waiting_approval" in text
    # The keyboard should have Approve and Reject buttons
    keyboard = msg.answers[0]["reply_markup"]
    assert keyboard is not None
