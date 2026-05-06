"""TG-03: Tests for /approve handler."""

from app.handlers import approve_handler as mod


class FakeApiClient:
    def __init__(self, *, task_return=None, approvals_return=None, get_task_fails: bool = False):
        self._task = task_return  # None = not found
        self._approvals = approvals_return or []
        self._get_task_fails = get_task_fails
        self._approve_calls = []
        self._get_task_calls = []
        self._find_calls = []

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

    async def list_approvals_by_task(self, task_id: str):
        return self._approvals

    async def approve_approval(self, approval_id: str, body=None):
        self._approve_calls.append((approval_id, body))
        return {"action": "deploy_staging", "status": "approved"}


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


async def test_approve_no_args(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/approve"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient())
    await mod.approve_handler(msg)
    assert "Usage" in msg.answers[0]["text"]


async def test_approve_task_not_found(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/approve task-9999"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(task_return=None))
    await mod.approve_handler(msg)
    assert "not found" in msg.answers[0]["text"].lower()


async def test_approve_no_pending(monkeypatch) -> None:
    task = {
        "id": "uuid-123",
        "external_id": "task-0001",
        "title": "Test",
        "status": "approved",
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
    msg.text = "/approve uuid-123"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(
        task_return=task,
        approvals_return=[{"id": "a1", "status": "approved", "action": "test"}],
    ))
    await mod.approve_handler(msg)
    assert "No pending approvals" in msg.answers[0]["text"]


async def test_approve_success(monkeypatch) -> None:
    task = {
        "id": "uuid-123",
        "external_id": "task-0001",
        "title": "Deploy task",
        "status": "waiting_approval",
        "risk_level": "medium",
        "intent": "deploy",
        "project_id": None,
        "agent_id": None,
        "plan_text": "Plan here",
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }
    fake = FakeApiClient(
        task_return=task,
        approvals_return=[{"id": "approval-1", "status": "pending", "action": "deploy_staging"}],
    )
    msg = FakeMessage()
    msg.text = "/approve uuid-123"
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.approve_handler(msg)
    # Should have approved
    assert len(fake._approve_calls) == 1
    assert fake._approve_calls[0][0] == "approval-1"
    # Confirmation message
    assert any("approved" in a["text"].lower() for a in msg.answers)
