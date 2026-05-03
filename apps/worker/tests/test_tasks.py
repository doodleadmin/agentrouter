"""Tests for all Celery task stubs + pipeline tasks."""

from unittest.mock import patch

from app.config import settings
from app.services.notifier import StubNotifier, set_notifier
from app.tasks.agent_execute import execute_task
from app.tasks.deploy import deploy_production, deploy_staging
from app.tasks.health import healthcheck
from app.tasks.memory_index import index_memory
from app.tasks.notifications import send_notification
from app.tasks.telegram_inbound import process_telegram_inbound

# ── healthcheck ──────────────────────────────────────────────────────────


def test_healthcheck() -> None:
    result = healthcheck()
    assert result["status"] == "ok"
    assert "broker" in result


# ── telegram_inbound ─────────────────────────────────────────────────────


def test_telegram_inbound_stub() -> None:
    result = process_telegram_inbound(chat_id=100, thread_id=5, text="hello", user_id=42)
    assert result["status"] == "stub"
    assert result["chat_id"] == 100
    assert result["thread_id"] == 5


# ── agent_execute ────────────────────────────────────────────────────────


def test_agent_execute_success() -> None:
    class FakeResponse:
        def __init__(self, payload: dict | None = None) -> None:
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            self.events: list[dict] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str) -> FakeResponse:
            assert "/tasks/task-0001" in url
            return FakeResponse(
                {
                    "id": "task-0001",
                    "external_id": "task-0001",
                    "status": "approved",
                    "payload": {"command": "pytest"},
                }
            )

        def patch(self, url: str, json: dict | None = None) -> FakeResponse:
            return FakeResponse({})

        def post(self, url: str, json: dict | None = None) -> FakeResponse:
            self.events.append(json or {})
            return FakeResponse({})

    with patch("app.tasks.agent_execute.httpx.Client", FakeClient):
        result = execute_task("task-0001")

    assert result["status"] == "completed"
    assert result["task_id"] == "task-0001"
    assert result["command"] == "pytest"


def test_agent_execute_status_gate_violation() -> None:
    class FakeResponse:
        def __init__(self, payload: dict | None = None) -> None:
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            self.events: list[dict] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str) -> FakeResponse:
            return FakeResponse({"id": "task-0002", "external_id": "task-0002", "status": "created", "payload": {}})

        def patch(self, url: str, json: dict | None = None) -> FakeResponse:
            return FakeResponse({})

        def post(self, url: str, json: dict | None = None) -> FakeResponse:
            self.events.append(json or {})
            return FakeResponse({})

    with patch("app.tasks.agent_execute.httpx.Client", FakeClient):
        result = execute_task("task-0002")

    assert result["status"] == "failed"
    assert result["event"] == "security_violation"


def test_agent_execute_command_policy_violation() -> None:
    class FakeResponse:
        def __init__(self, payload: dict | None = None) -> None:
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            self.events: list[dict] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str) -> FakeResponse:
            return FakeResponse({
                "id": "task-0003",
                "external_id": "task-0003",
                "status": "approved",
                "payload": {"command": "docker compose up"},
            })

        def patch(self, url: str, json: dict | None = None) -> FakeResponse:
            return FakeResponse({})

        def post(self, url: str, json: dict | None = None) -> FakeResponse:
            self.events.append(json or {})
            return FakeResponse({})

    with patch("app.tasks.agent_execute.httpx.Client", FakeClient):
        result = execute_task("task-0003")

    assert result["status"] == "failed"
    assert result["event"] == "security_violation"


def test_agent_execute_docker_mode_unavailable_returns_sandbox_error() -> None:
    class FakeResponse:
        def __init__(self, payload: dict | None = None) -> None:
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            self.events: list[dict] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str) -> FakeResponse:
            return FakeResponse(
                {
                    "id": "task-0004",
                    "external_id": "task-0004",
                    "status": "approved",
                    "payload": {"command": "pytest"},
                }
            )

        def patch(self, url: str, json: dict | None = None) -> FakeResponse:
            return FakeResponse({})

        def post(self, url: str, json: dict | None = None) -> FakeResponse:
            self.events.append(json or {})
            return FakeResponse({})

    original_mode = settings.SANDBOX_RUNNER_MODE
    settings.SANDBOX_RUNNER_MODE = "docker"
    try:
        with patch("app.tasks.agent_execute.httpx.Client", FakeClient):
            result = execute_task("task-0004")
    finally:
        settings.SANDBOX_RUNNER_MODE = original_mode

    assert result["status"] == "failed"
    assert result["event"] == "sandbox_error"


def test_agent_execute_docker_mode_unavailable_redacts_error_details() -> None:
    from app.services.sandbox_runner import DockerUnavailableError

    class FakeResponse:
        def __init__(self, payload: dict | None = None) -> None:
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            self.events: list[dict] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str) -> FakeResponse:
            return FakeResponse(
                {
                    "id": "task-0005",
                    "external_id": "task-0005",
                    "status": "approved",
                    "payload": {"command": "pytest"},
                }
            )

        def patch(self, url: str, json: dict | None = None) -> FakeResponse:
            return FakeResponse({})

        def post(self, url: str, json: dict | None = None) -> FakeResponse:
            self.events.append(json or {})
            return FakeResponse({})

    original_mode = settings.SANDBOX_RUNNER_MODE
    settings.SANDBOX_RUNNER_MODE = "docker"
    try:
        with (
            patch("app.tasks.agent_execute.httpx.Client", FakeClient),
            patch(
                "app.tasks.agent_execute.DockerSandboxRunner.run",
                side_effect=DockerUnavailableError("docker unavailable token=abc123"),
            ),
        ):
            result = execute_task("task-0005")
    finally:
        settings.SANDBOX_RUNNER_MODE = original_mode

    assert result["status"] == "failed"
    assert result["event"] == "sandbox_error"
    assert "abc123" not in str(result.get("reason", ""))


# ── memory_index ─────────────────────────────────────────────────────────


def test_memory_index_success() -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "scope": "project",
                "project_slug": "academy-bot",
                "scanned_files": 7,
                "indexed_documents": 7,
                "skipped_documents": 0,
                "total_chunks": 21,
            }

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url: str, json: dict | None = None) -> FakeResponse:
            assert url.endswith("/memory/reindex")
            assert json is not None
            assert json["scope"] == "project"
            assert json["project_slug"] == "academy-bot"
            return FakeResponse()

    with patch("app.tasks.memory_index.httpx.Client", FakeClient):
        result = index_memory(scope="project", project_slug="academy-bot")

    assert result["status"] == "ok"
    assert result["scope"] == "project"
    assert result["project_slug"] == "academy-bot"
    assert result["scanned_files"] == 7
    assert result["total_chunks"] == 21


def test_memory_index_http_error() -> None:
    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url: str, json: dict | None = None):
            raise Exception("boom")

    # Raise httpx.HTTPError specifically, to match task handler
    import httpx

    class ErrorClient(FakeClient):
        def post(self, url: str, json: dict | None = None):
            raise httpx.HTTPError("network")

    with patch("app.tasks.memory_index.httpx.Client", ErrorClient):
        result = index_memory(scope="all")

    assert result["status"] == "error"
    assert result["scope"] == "all"
    assert "error" in result


# ── deploy_staging ───────────────────────────────────────────────────────


def test_deploy_staging_stub() -> None:
    result = deploy_staging(project_slug="academy-bot", branch="main")
    assert result["status"] == "stub"
    assert result["environment"] == "staging"
    assert result["project_slug"] == "academy-bot"


# ── deploy_production ────────────────────────────────────────────────────


def test_deploy_production_blocked() -> None:
    result = deploy_production(project_slug="academy-bot", branch="main")
    assert result["status"] == "blocked"
    assert result["environment"] == "production"
    assert "approval" in result["message"].lower() or "blocked" in result["message"].lower()


# ── notifications (with stub notifier) ───────────────────────────────────


def test_send_notification_with_stub_notifier() -> None:
    stub = StubNotifier()
    set_notifier(stub)

    result = send_notification(
        notification_type="plan_ready",
        chat_id=100,
        thread_id=5,
        message="Plan is ready!",
    )
    assert result["status"] == "ok"
    assert result["notification_type"] == "plan_ready"
    assert len(stub.sent) == 1
    assert stub.sent[0]["chat_id"] == 100
    assert stub.sent[0]["thread_id"] == 5
    assert stub.sent[0]["text"] == "Plan is ready!"


def test_send_notification_skipped_no_chat_id() -> None:
    result = send_notification(
        notification_type="plan_ready",
        chat_id=None,
        message="test",
    )
    assert result["status"] == "skipped"
