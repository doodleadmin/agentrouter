"""TG-03: Tests for callback query handler."""

from app.handlers import callbacks as mod


class FakeApiClient:
    def __init__(self, *, task_return=None, approvals_return=None, plan_return=None,
                 cb_result=None, approve_ok=True, reject_ok=True):
        self._task = task_return or {}
        self._approvals = approvals_return or []
        self._plan = plan_return or {}
        self._cb_result = cb_result or {"action_valid": True, "action": "refresh", "approval_id": None}
        self._approve_ok = approve_ok
        self._reject_ok = reject_ok
        self._approve_calls = []
        self._reject_calls = []
        self._cb_calls = []

    async def get_task(self, task_id: str):
        return self._task

    async def get_task_plan(self, task_id: str):
        return self._plan

    async def list_approvals_by_task(self, task_id: str):
        return self._approvals

    async def approve_approval(self, approval_id: str, body=None):
        self._approve_calls.append((approval_id, body))
        if not self._approve_ok:
            raise RuntimeError("approve failed")
        return {"action": "test", "status": "approved"}

    async def reject_approval(self, approval_id: str, body=None):
        self._reject_calls.append((approval_id, body))
        if not self._reject_ok:
            raise RuntimeError("reject failed")
        return {"action": "test", "status": "rejected"}

    async def callback_answer(self, task_id: str, body):
        self._cb_calls.append((task_id, body))
        return self._cb_result


class FakeCallbackQuery:
    def __init__(self, data: str, chat_id: int = 123, thread_id: int = 0, user_id: int = 999):
        self.data = data
        self._chat_id = chat_id
        self._thread_id = thread_id
        self._user_id = user_id
        self.message = FakeMessage(chat_id, thread_id)
        self.from_user = FakeUser(user_id)
        self.answers = []

    async def answer(self, text: str = "", show_alert: bool = False):
        self.answers.append({"text": text, "show_alert": show_alert})


class FakeMessage:
    def __init__(self, chat_id, thread_id):
        self.chat = FakeChat(chat_id)
        self.message_thread_id = thread_id

    async def edit_text(self, text, reply_markup=None, parse_mode=None):
        pass  # No-op for tests


class FakeChat:
    def __init__(self, chat_id):
        self.id = chat_id
        self.type = "supergroup"


class FakeUser:
    def __init__(self, user_id):
        self.id = user_id
        self.username = "testuser"


async def test_callback_empty_data(monkeypatch) -> None:
    query = FakeCallbackQuery("")
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient())
    await mod.handle_callback(query)
    assert query.answers[0]["text"] == "No callback data"


async def test_callback_invalid_task_id(monkeypatch) -> None:
    query = FakeCallbackQuery("garbage|data")
    monkeypatch.setattr(mod, "get_api_client", lambda: FakeApiClient())
    await mod.handle_callback(query)
    assert "Invalid" in query.answers[0]["text"]


async def test_callback_validation_rejected(monkeypatch) -> None:
    cb_data = "1|show_plan|550e8400-e29b-41d4-a716-446655440000|none|1|9999999999|badsig"
    query = FakeCallbackQuery(cb_data)
    fake = FakeApiClient(cb_result={
        "action_valid": False,
        "action": "show_plan",
        "error": "Invalid signature",
    })
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.handle_callback(query)
    assert len(fake._cb_calls) == 1
    # Should show alert with error
    assert any("rejected" in a["text"].lower() or "Invalid" in a["text"] for a in query.answers)


async def test_callback_refresh_action(monkeypatch) -> None:
    cb_data = "1|refresh|550e8400-e29b-41d4-a716-446655440000|none|1|9999999999|test"
    query = FakeCallbackQuery(cb_data)
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
    fake = FakeApiClient(
        task_return=task,
        cb_result={"action_valid": True, "action": "refresh", "approval_id": None},
    )
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.handle_callback(query)
    assert len(fake._cb_calls) == 1
    # Should have called answer("Refreshed")
    assert any("Refreshed" in a["text"] for a in query.answers)


async def test_callback_approve_action(monkeypatch) -> None:
    cb_data = "1|approve|550e8400-e29b-41d4-a716-446655440000|approval-1|1|9999999999|test"
    query = FakeCallbackQuery(cb_data)
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0001",
        "title": "Test task",
        "status": "waiting_approval",
        "risk_level": "medium",
        "intent": None,
        "project_id": None,
        "agent_id": None,
        "plan_text": "Plan",
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }
    fake = FakeApiClient(
        task_return=task,
        cb_result={"action_valid": True, "action": "approve", "approval_id": "approval-1"},
        approve_ok=True,
    )
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.handle_callback(query)
    assert len(fake._approve_calls) == 1
    assert fake._approve_calls[0][0] == "approval-1"


async def test_callback_approve_no_approval_id(monkeypatch) -> None:
    cb_data = "1|approve|550e8400-e29b-41d4-a716-446655440000|none|1|9999999999|test"
    query = FakeCallbackQuery(cb_data)
    fake = FakeApiClient(
        cb_result={"action_valid": True, "action": "approve", "approval_id": None},
    )
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.handle_callback(query)
    # Should show alert about no pending approval
    assert any("No pending" in a["text"] for a in query.answers)


async def test_callback_reject_action(monkeypatch) -> None:
    cb_data = "1|reject|550e8400-e29b-41d4-a716-446655440000|approval-2|1|9999999999|test"
    query = FakeCallbackQuery(cb_data)
    task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "task-0001",
        "title": "Test task",
        "status": "waiting_approval",
        "risk_level": "high",
        "intent": None,
        "project_id": None,
        "agent_id": None,
        "plan_text": None,
        "result_summary": None,
        "payload": {},
        "created_at": "2026-05-05T12:00:00.000Z",
        "updated_at": "2026-05-05T12:00:00.000Z",
    }
    fake = FakeApiClient(
        task_return=task,
        cb_result={"action_valid": True, "action": "reject", "approval_id": "approval-2"},
        reject_ok=True,
    )
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.handle_callback(query)
    assert len(fake._reject_calls) == 1
    assert fake._reject_calls[0][0] == "approval-2"


async def test_callback_show_plan_action(monkeypatch) -> None:
    cb_data = "1|show_plan|550e8400-e29b-41d4-a716-446655440000|none|1|9999999999|test"
    query = FakeCallbackQuery(cb_data)
    fake = FakeApiClient(
        plan_return={"task_id": "550e8400-e29b-41d4-a716-446655440000", "plan_text": "Step 1: Do X", "plan_version": 1, "status": "approved"},
        cb_result={"action_valid": True, "action": "show_plan", "approval_id": None},
    )
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.handle_callback(query)
    # Should have fetched plan and edited message (no-op in test)
    assert len(fake._cb_calls) == 1


async def test_callback_unknown_action(monkeypatch) -> None:
    cb_data = "1|unknown|550e8400-e29b-41d4-a716-446655440000|none|1|9999999999|test"
    query = FakeCallbackQuery(cb_data)
    fake = FakeApiClient(
        cb_result={"action_valid": True, "action": "unknown", "approval_id": None},
    )
    monkeypatch.setattr(mod, "get_api_client", lambda: fake)
    await mod.handle_callback(query)
    assert any("unknown" in a["text"].lower() or "Unknown" in a["text"] for a in query.answers)
