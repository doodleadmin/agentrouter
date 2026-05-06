"""TG-03: Tests for /reject handler."""

from app.handlers import reject_handler as mod


class FakeApiClient:
    def __init__(self, *, task_return=None, approvals_return=None, get_task_fails: bool = False):
        self._task = task_return  # None = not found
        self._approvals = approvals_return or []
        self._get_task_fails = get_task_fails
        self._reject_calls = []
        self._find_calls = []

    async def get_task(self, task_id: str):
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

    async def reject_approval(self, approval_id: str, body=None):
        self._reject_calls.append((approval_id, body))
        action = (body or {}).get("action") or "deploy_staging"
        return {"action": action, "status": "rejected"}


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


async def test_reject_no_args(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/reject"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient())
    await mod.reject_handler(msg)
    assert "Usage" in msg.answers[0]["text"]


async def test_reject_task_not_found(monkeypatch) -> None:
    msg = FakeMessage()
    msg.text = "/reject task-9999"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(task_return=None))
    await mod.reject_handler(msg)
    assert "not found" in msg.answers[0]["text"].lower()


async def test_reject_no_pending(monkeypatch) -> None:
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
    msg.text = "/reject uuid-123"
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient(
        task_return=task,
        approvals_return=[{"id": "a1", "status": "approved", "action": "test"}],
    ))
    await mod.reject_handler(msg)
    assert "No pending approvals" in msg.answers[0]["text"]


async def test_reject_success(monkeypatch) -> None:
    task = {
        "id": "uuid-123",
        "external_id": "task-0001",
        "title": "Deploy task",
        "status": "waiting_approval",
        "risk_level": "high",
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
        approvals_return=[{"id": "approval-1", "status": "pending", "action": "deploy_production"}],
    )
    msg = FakeMessage()
    msg.text = "/reject uuid-123 too dangerous"
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.reject_handler(msg)
    assert len(fake._reject_calls) == 1
    assert fake._reject_calls[0][0] == "approval-1"
    assert fake._reject_calls[0][1]["reason"] == "too dangerous"
    assert any("rejected" in a["text"].lower() for a in msg.answers)
